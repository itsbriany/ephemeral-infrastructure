"""DynamoDB adapter for the persistent environment registry."""

import hashlib
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any, Protocol

from ephemeral_environments.environment import EnvironmentRecord
from ephemeral_environments.lifecycle import EnvironmentStatus, can_transition, require_transition
from ephemeral_environments.repository import (
    EnvironmentNotFound,
    IdempotencyConflict,
    Reservation,
)


class DynamoDbClient(Protocol):
    def transact_write_items(self, **kwargs: Any) -> Mapping[str, Any]: ...

    def get_item(self, **kwargs: Any) -> Mapping[str, Any]: ...

    def update_item(self, **kwargs: Any) -> Mapping[str, Any]: ...


class RegistryConsistencyError(RuntimeError):
    """Raised when related registry records are unexpectedly inconsistent."""


class DynamoEnvironmentRepository:
    """Persist environment and idempotency records in one DynamoDB table."""

    def __init__(self, client: DynamoDbClient, table_name: str) -> None:
        self._client = client
        self._table_name = table_name

    def reserve(
        self,
        *,
        environment_id: str,
        application_id: str,
        idempotency_key: str,
        now: datetime | None = None,
    ) -> Reservation:
        timestamp = now or datetime.now(UTC)
        record = EnvironmentRecord.requested(
            environment_id=environment_id,
            application_id=application_id,
            now=timestamp,
        )
        marker_key = self._idempotency_partition_key(idempotency_key)

        try:
            self._client.transact_write_items(
                TransactItems=[
                    {
                        "Put": {
                            "TableName": self._table_name,
                            "Item": self._environment_item(record),
                            "ConditionExpression": "attribute_not_exists(pk)",
                        }
                    },
                    {
                        "Put": {
                            "TableName": self._table_name,
                            "Item": {
                                "pk": {"S": marker_key},
                                "entityType": {"S": "IDEMPOTENCY"},
                                "applicationId": {"S": application_id},
                                "environmentId": {"S": environment_id},
                                "createdAt": {"S": timestamp.isoformat()},
                            },
                            "ConditionExpression": "attribute_not_exists(pk)",
                        }
                    },
                ]
            )
        except Exception as error:
            if self._error_code(error) != "TransactionCanceledException":
                raise

            marker = self._get_item(marker_key)
            if marker is None:
                raise

            if self._string(marker, "applicationId") != application_id:
                raise IdempotencyConflict(
                    "Idempotency-Key was already used for a different request"
                ) from error

            existing_environment_id = self._string(marker, "environmentId")
            existing = self._get_item(self._environment_partition_key(existing_environment_id))
            if existing is None:
                raise RegistryConsistencyError(
                    "Idempotency record references a missing environment"
                ) from error
            return Reservation(self._environment_record(existing), created=False)

        return Reservation(record, created=True)

    def get(self, environment_id: str) -> EnvironmentRecord:
        item = self._get_item(self._environment_partition_key(environment_id))
        if item is None:
            raise EnvironmentNotFound(environment_id)
        return self._environment_record(item)

    def request_termination(
        self,
        environment_id: str,
        *,
        now: datetime | None = None,
    ) -> tuple[EnvironmentRecord, bool]:
        timestamp = now or datetime.now(UTC)
        current_states = tuple(
            status
            for status in EnvironmentStatus
            if can_transition(status, EnvironmentStatus.TERMINATING)
        )
        values = {
            ":target": {"S": EnvironmentStatus.TERMINATING.value},
            ":updatedAt": {"S": timestamp.isoformat()},
            **{
                f":current{index}": {"S": status.value}
                for index, status in enumerate(current_states)
            },
        }
        allowed = ", ".join(f":current{index}" for index in range(len(current_states)))

        try:
            response = self._client.update_item(
                TableName=self._table_name,
                Key={"pk": {"S": self._environment_partition_key(environment_id)}},
                ConditionExpression=f"attribute_exists(pk) AND #status IN ({allowed})",
                UpdateExpression="SET #status = :target, updatedAt = :updatedAt REMOVE endpoint",
                ExpressionAttributeNames={"#status": "status"},
                ExpressionAttributeValues=values,
                ReturnValues="ALL_NEW",
            )
        except Exception as error:
            if self._error_code(error) != "ConditionalCheckFailedException":
                raise

            existing = self._get_item(self._environment_partition_key(environment_id))
            if existing is None:
                raise EnvironmentNotFound(environment_id) from error

            record = self._environment_record(existing)
            if record.status in {EnvironmentStatus.TERMINATING, EnvironmentStatus.DESTROYED}:
                return record, False

            require_transition(record.status, EnvironmentStatus.TERMINATING)
            raise RegistryConsistencyError(
                "Conditional lifecycle update was not applied"
            ) from error

        attributes = response.get("Attributes")
        if not isinstance(attributes, Mapping):
            raise RegistryConsistencyError("DynamoDB update did not return the updated record")
        return self._environment_record(attributes), True

    def _get_item(self, partition_key: str) -> Mapping[str, Any] | None:
        response = self._client.get_item(
            TableName=self._table_name,
            Key={"pk": {"S": partition_key}},
            ConsistentRead=True,
        )
        item = response.get("Item")
        return item if isinstance(item, Mapping) else None

    @classmethod
    def _environment_item(cls, record: EnvironmentRecord) -> dict[str, dict[str, str]]:
        item = {
            "pk": {"S": cls._environment_partition_key(record.environment_id)},
            "entityType": {"S": "ENVIRONMENT"},
            "environmentId": {"S": record.environment_id},
            "applicationId": {"S": record.application_id},
            "status": {"S": record.status.value},
            "createdAt": {"S": record.created_at.isoformat()},
            "updatedAt": {"S": record.updated_at.isoformat()},
        }
        if record.ready_at is not None:
            item["readyAt"] = {"S": record.ready_at.isoformat()}
        if record.destroyed_at is not None:
            item["destroyedAt"] = {"S": record.destroyed_at.isoformat()}
        if record.endpoint is not None:
            item["endpoint"] = {"S": record.endpoint}
        return item

    @classmethod
    def _environment_record(cls, item: Mapping[str, Any]) -> EnvironmentRecord:
        ready_at = cls._optional_string(item, "readyAt")
        destroyed_at = cls._optional_string(item, "destroyedAt")
        return EnvironmentRecord(
            environment_id=cls._string(item, "environmentId"),
            application_id=cls._string(item, "applicationId"),
            status=EnvironmentStatus(cls._string(item, "status")),
            created_at=datetime.fromisoformat(cls._string(item, "createdAt")),
            updated_at=datetime.fromisoformat(cls._string(item, "updatedAt")),
            ready_at=datetime.fromisoformat(ready_at) if ready_at else None,
            destroyed_at=datetime.fromisoformat(destroyed_at) if destroyed_at else None,
            endpoint=cls._optional_string(item, "endpoint"),
        )

    @staticmethod
    def _string(item: Mapping[str, Any], name: str) -> str:
        attribute = item.get(name)
        if not isinstance(attribute, Mapping) or not isinstance(attribute.get("S"), str):
            raise RegistryConsistencyError(f"Registry item has invalid {name}")
        return attribute["S"]

    @classmethod
    def _optional_string(cls, item: Mapping[str, Any], name: str) -> str | None:
        return cls._string(item, name) if name in item else None

    @staticmethod
    def _environment_partition_key(environment_id: str) -> str:
        return f"ENVIRONMENT#{environment_id}"

    @staticmethod
    def _idempotency_partition_key(idempotency_key: str) -> str:
        digest = hashlib.sha256(idempotency_key.encode()).hexdigest()
        return f"IDEMPOTENCY#{digest}"

    @staticmethod
    def _error_code(error: Exception) -> str | None:
        response = getattr(error, "response", None)
        if not isinstance(response, Mapping):
            return None
        details = response.get("Error")
        if not isinstance(details, Mapping):
            return None
        code = details.get("Code")
        return code if isinstance(code, str) else None
