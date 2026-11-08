from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

import pytest

from ephemeral_environments.aws_repository import DynamoEnvironmentRepository
from ephemeral_environments.lifecycle import EnvironmentStatus
from ephemeral_environments.repository import EnvironmentNotFound, IdempotencyConflict


class FakeAwsError(Exception):
    def __init__(self, code: str) -> None:
        self.response = {"Error": {"Code": code}}
        super().__init__(code)


class FakeDynamoDbClient:
    def __init__(self) -> None:
        self.items: dict[str, dict[str, Any]] = {}
        self.last_transaction: list[dict[str, Any]] | None = None

    def transact_write_items(self, **kwargs: Any) -> Mapping[str, Any]:
        transaction = kwargs["TransactItems"]
        self.last_transaction = transaction
        if any(operation["Put"]["Item"]["pk"]["S"] in self.items for operation in transaction):
            raise FakeAwsError("TransactionCanceledException")
        for operation in transaction:
            item = operation["Put"]["Item"]
            self.items[item["pk"]["S"]] = item
        return {}

    def get_item(self, **kwargs: Any) -> Mapping[str, Any]:
        item = self.items.get(kwargs["Key"]["pk"]["S"])
        return {"Item": item} if item is not None else {}

    def update_item(self, **kwargs: Any) -> Mapping[str, Any]:
        key = kwargs["Key"]["pk"]["S"]
        item = self.items.get(key)
        allowed = {
            value["S"]
            for name, value in kwargs["ExpressionAttributeValues"].items()
            if name.startswith(":current")
        }
        if item is None or item["status"]["S"] not in allowed:
            raise FakeAwsError("ConditionalCheckFailedException")
        item["status"] = kwargs["ExpressionAttributeValues"][":target"]
        item["updatedAt"] = kwargs["ExpressionAttributeValues"][":updatedAt"]
        item.pop("endpoint", None)
        return {"Attributes": item}


NOW = datetime(2026, 11, 8, 12, 0, tzinfo=UTC)


def test_reserve_atomically_writes_environment_and_hashed_idempotency_marker() -> None:
    client = FakeDynamoDbClient()
    repository = DynamoEnvironmentRepository(client, "registry")

    reservation = repository.reserve(
        environment_id="env-first",
        application_id="hello-environment",
        idempotency_key="synthetic-request-key",
        now=NOW,
    )

    assert reservation.created is True
    assert reservation.record.status is EnvironmentStatus.REQUESTED
    assert len(client.items) == 2
    assert "ENVIRONMENT#env-first" in client.items
    marker_key = next(key for key in client.items if key.startswith("IDEMPOTENCY#"))
    assert marker_key != "IDEMPOTENCY#synthetic-request-key"
    assert "synthetic-request-key" not in repr(client.last_transaction)
    assert all(
        operation["Put"]["ConditionExpression"] == "attribute_not_exists(pk)"
        for operation in client.last_transaction or []
    )


def test_duplicate_reservation_replays_the_original_environment() -> None:
    client = FakeDynamoDbClient()
    repository = DynamoEnvironmentRepository(client, "registry")
    first = repository.reserve(
        environment_id="env-first",
        application_id="hello-environment",
        idempotency_key="repeat-key",
        now=NOW,
    )

    replay = repository.reserve(
        environment_id="env-second",
        application_id="hello-environment",
        idempotency_key="repeat-key",
        now=NOW,
    )

    assert first.created is True
    assert replay.created is False
    assert replay.record.environment_id == "env-first"
    assert "ENVIRONMENT#env-second" not in client.items


def test_idempotency_key_cannot_be_reused_for_another_application() -> None:
    client = FakeDynamoDbClient()
    repository = DynamoEnvironmentRepository(client, "registry")
    repository.reserve(
        environment_id="env-first",
        application_id="hello-environment",
        idempotency_key="repeat-key",
        now=NOW,
    )

    with pytest.raises(IdempotencyConflict, match="different request"):
        repository.reserve(
            environment_id="env-second",
            application_id="another-application",
            idempotency_key="repeat-key",
            now=NOW,
        )


def test_termination_is_conditional_and_idempotent() -> None:
    client = FakeDynamoDbClient()
    repository = DynamoEnvironmentRepository(client, "registry")
    repository.reserve(
        environment_id="env-first",
        application_id="hello-environment",
        idempotency_key="termination-key",
        now=NOW,
    )

    first, started = repository.request_termination("env-first", now=NOW)
    replay, replay_started = repository.request_termination("env-first", now=NOW)

    assert started is True
    assert replay_started is False
    assert first.status is replay.status is EnvironmentStatus.TERMINATING


def test_missing_environment_is_not_found() -> None:
    repository = DynamoEnvironmentRepository(FakeDynamoDbClient(), "registry")

    with pytest.raises(EnvironmentNotFound):
        repository.get("env-missing")
    with pytest.raises(EnvironmentNotFound):
        repository.request_termination("env-missing", now=NOW)
