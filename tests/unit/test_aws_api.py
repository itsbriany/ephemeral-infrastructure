import json
import logging
from datetime import UTC, datetime
from typing import Any

import pytest

from ephemeral_environments import aws_api
from ephemeral_environments.environment import EnvironmentRecord
from ephemeral_environments.lifecycle import EnvironmentStatus
from ephemeral_environments.repository import EnvironmentNotFound, Reservation

NOW = datetime(2026, 11, 8, 12, 0, tzinfo=UTC)


class StubRepository:
    record = EnvironmentRecord.requested(
        environment_id="env-test",
        application_id="hello-environment",
        now=NOW,
    )

    def reserve(self, **_kwargs: Any) -> Reservation:
        return Reservation(self.record, created=True)

    def get(self, environment_id: str) -> EnvironmentRecord:
        if environment_id == "env-missing":
            raise EnvironmentNotFound(environment_id)
        return self.record

    def request_termination(self, environment_id: str) -> tuple[EnvironmentRecord, bool]:
        if environment_id == "env-missing":
            raise EnvironmentNotFound(environment_id)
        return self.record.with_status(EnvironmentStatus.TERMINATING, now=NOW), True


def _event(**overrides: Any) -> dict[str, Any]:
    event: dict[str, Any] = {
        "requestContext": {"requestId": "api-request-001"},
        "headers": {"idempotency-key": "synthetic-key"},
        "body": json.dumps({"applicationId": "hello-environment"}),
        "pathParameters": {"environmentId": "env-test"},
        "isBase64Encoded": False,
    }
    event.update(overrides)
    return event


def _body(response: dict[str, Any]) -> Any:
    return json.loads(response["body"])


def test_lists_only_approved_applications() -> None:
    response = aws_api.list_applications(_event(), None)

    assert response["statusCode"] == 200
    assert _body(response) == [
        {
            "applicationId": "hello-environment",
            "displayName": "Hello Environment",
            "sessionMinutes": 15,
            "maxLifetimeMinutes": 30,
        }
    ]


def test_create_persists_a_request_and_logs_only_safe_correlation_fields(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(aws_api, "_repository", StubRepository)
    caplog.set_level(logging.INFO, logger=aws_api.__name__)

    response = aws_api.create_environment(_event(), None)

    assert response["statusCode"] == 202
    assert response["headers"]["Idempotency-Replayed"] == "false"
    assert _body(response)["status"] == "REQUESTED"
    assert "api-request-001" in caplog.text
    assert "env-test" in caplog.text
    assert "synthetic-key" not in caplog.text


@pytest.mark.parametrize(
    ("event", "expected_status"),
    [
        (_event(headers={}), 422),
        (_event(body="not-json"), 400),
        (_event(body=json.dumps([])), 400),
        (_event(body=json.dumps({"applicationId": "unknown"})), 422),
        (_event(isBase64Encoded=True), 400),
    ],
)
def test_create_rejects_invalid_public_input(
    monkeypatch: pytest.MonkeyPatch,
    event: dict[str, Any],
    expected_status: int,
) -> None:
    monkeypatch.setattr(aws_api, "_repository", StubRepository)

    assert aws_api.create_environment(event, None)["statusCode"] == expected_status


def test_get_and_terminate_use_the_path_environment_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(aws_api, "_repository", StubRepository)

    retrieved = aws_api.get_environment(_event(), None)
    terminated = aws_api.terminate_environment(_event(), None)

    assert retrieved["statusCode"] == 200
    assert _body(retrieved)["environmentId"] == "env-test"
    assert terminated["statusCode"] == 202
    assert _body(terminated)["status"] == "TERMINATING"


def test_unknown_environment_returns_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(aws_api, "_repository", StubRepository)
    event = _event(pathParameters={"environmentId": "env-missing"})

    assert aws_api.get_environment(event, None)["statusCode"] == 404
    assert aws_api.terminate_environment(event, None)["statusCode"] == 404
