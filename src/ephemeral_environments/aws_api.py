"""API Gateway HTTP API handlers for the persistent AWS control plane."""

import json
import logging
import os
from collections.abc import Callable, Mapping
from datetime import datetime
from typing import Any
from uuid import uuid4

from ephemeral_environments.application_profiles import APPLICATION_CATALOG
from ephemeral_environments.aws_repository import (
    DynamoEnvironmentRepository,
    RegistryConsistencyError,
)
from ephemeral_environments.environment import EnvironmentRecord
from ephemeral_environments.lifecycle import InvalidLifecycleTransition
from ephemeral_environments.repository import EnvironmentNotFound, IdempotencyConflict

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)

_DYNAMODB_CLIENT: object | None = None


def list_applications(event: Mapping[str, Any], _context: object) -> dict[str, Any]:
    def operation() -> dict[str, Any]:
        applications = [
            {
                "applicationId": profile.application_id,
                "displayName": profile.display_name,
                "sessionMinutes": profile.session_minutes,
                "maxLifetimeMinutes": profile.max_lifetime_minutes,
            }
            for profile in APPLICATION_CATALOG.values()
        ]
        _log(event, "approved_applications_listed")
        return _response(200, applications)

    return _handle(event, operation)


def create_environment(event: Mapping[str, Any], _context: object) -> dict[str, Any]:
    def operation() -> dict[str, Any]:
        body = _json_body(event)
        application_id = body.get("applicationId")
        if not isinstance(application_id, str) or application_id not in APPLICATION_CATALOG:
            return _response(422, {"detail": "Application is not approved"})

        idempotency_key = _header(event, "idempotency-key")
        if idempotency_key is None or not idempotency_key.strip():
            return _response(422, {"detail": "Idempotency-Key is required"})
        idempotency_key = idempotency_key.strip()
        if len(idempotency_key) > 128:
            return _response(422, {"detail": "Idempotency-Key is too long"})

        reservation = _repository().reserve(
            environment_id=f"env-{uuid4().hex[:12]}",
            application_id=application_id,
            idempotency_key=idempotency_key,
        )
        _log(
            event,
            "environment_request_persisted",
            environment_id=reservation.record.environment_id,
            status=reservation.record.status.value,
            replayed=not reservation.created,
        )
        return _response(
            202,
            _environment_body(reservation.record),
            headers={"Idempotency-Replayed": str(not reservation.created).lower()},
        )

    return _handle(event, operation)


def get_environment(event: Mapping[str, Any], _context: object) -> dict[str, Any]:
    def operation() -> dict[str, Any]:
        environment_id = _path_parameter(event, "environmentId")
        record = _repository().get(environment_id)
        _log(
            event,
            "environment_retrieved",
            environment_id=record.environment_id,
            status=record.status.value,
        )
        return _response(200, _environment_body(record))

    return _handle(event, operation)


def terminate_environment(event: Mapping[str, Any], _context: object) -> dict[str, Any]:
    def operation() -> dict[str, Any]:
        environment_id = _path_parameter(event, "environmentId")
        record, started = _repository().request_termination(environment_id)
        _log(
            event,
            "environment_termination_persisted",
            environment_id=record.environment_id,
            status=record.status.value,
            replayed=not started,
        )
        return _response(202, _environment_body(record))

    return _handle(event, operation)


def _handle(
    event: Mapping[str, Any],
    operation: Callable[[], dict[str, Any]],
) -> dict[str, Any]:
    try:
        return operation()
    except InvalidRequest as error:
        return _response(400, {"detail": str(error)})
    except EnvironmentNotFound:
        return _response(404, {"detail": "Environment not found"})
    except (IdempotencyConflict, InvalidLifecycleTransition) as error:
        return _response(409, {"detail": str(error)})
    except Exception as error:
        _log(event, "control_plane_request_failed", error_type=type(error).__name__)
        LOGGER.exception("Control-plane request failed")
        return _response(500, {"detail": "Internal server error"})


class InvalidRequest(ValueError):
    """Raised when an API Gateway event does not contain valid public input."""


def _repository() -> DynamoEnvironmentRepository:
    global _DYNAMODB_CLIENT

    table_name = os.environ.get("ENVIRONMENTS_TABLE_NAME")
    if not table_name:
        raise RegistryConsistencyError("ENVIRONMENTS_TABLE_NAME is not configured")

    if _DYNAMODB_CLIENT is None:
        import boto3

        _DYNAMODB_CLIENT = boto3.client("dynamodb")
    return DynamoEnvironmentRepository(_DYNAMODB_CLIENT, table_name)  # type: ignore[arg-type]


def _json_body(event: Mapping[str, Any]) -> Mapping[str, Any]:
    if event.get("isBase64Encoded"):
        raise InvalidRequest("Base64-encoded request bodies are not supported")
    body = event.get("body")
    if not isinstance(body, str):
        raise InvalidRequest("Request body must be JSON")
    try:
        decoded = json.loads(body)
    except json.JSONDecodeError as error:
        raise InvalidRequest("Request body must be valid JSON") from error
    if not isinstance(decoded, Mapping):
        raise InvalidRequest("Request body must be a JSON object")
    return decoded


def _header(event: Mapping[str, Any], name: str) -> str | None:
    headers = event.get("headers")
    if not isinstance(headers, Mapping):
        return None
    for candidate, value in headers.items():
        if isinstance(candidate, str) and candidate.lower() == name and isinstance(value, str):
            return value
    return None


def _path_parameter(event: Mapping[str, Any], name: str) -> str:
    parameters = event.get("pathParameters")
    if not isinstance(parameters, Mapping) or not isinstance(parameters.get(name), str):
        raise InvalidRequest(f"Missing path parameter: {name}")
    return parameters[name]


def _environment_body(record: EnvironmentRecord) -> dict[str, Any]:
    return {
        "environmentId": record.environment_id,
        "applicationId": record.application_id,
        "status": record.status.value,
        "createdAt": record.created_at.isoformat(),
        "updatedAt": record.updated_at.isoformat(),
        "readyAt": _timestamp(record.ready_at),
        "destroyedAt": _timestamp(record.destroyed_at),
        "endpoint": record.endpoint,
    }


def _timestamp(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _response(
    status_code: int,
    body: object,
    *,
    headers: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", **(headers or {})},
        "body": json.dumps(body, separators=(",", ":")),
        "isBase64Encoded": False,
    }


def _log(
    event: Mapping[str, Any],
    event_name: str,
    *,
    environment_id: str | None = None,
    status: str | None = None,
    replayed: bool | None = None,
    error_type: str | None = None,
) -> None:
    request_context = event.get("requestContext")
    request_id = request_context.get("requestId") if isinstance(request_context, Mapping) else None
    entry: dict[str, object] = {
        "event": event_name,
        "apiRequestId": request_id if isinstance(request_id, str) else "unavailable",
    }
    if environment_id is not None:
        entry["environmentId"] = environment_id
    if status is not None:
        entry["status"] = status
    if replayed is not None:
        entry["replayed"] = replayed
    if error_type is not None:
        entry["errorType"] = error_type
    LOGGER.info(json.dumps(entry, separators=(",", ":")))
