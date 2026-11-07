import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
from asgi_lifespan import LifespanManager
from httpx2 import ASGITransport, AsyncClient

from ephemeral_environments.api import create_app
from ephemeral_environments.repository import (
    IdempotencyConflict,
    InMemoryEnvironmentRepository,
)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@asynccontextmanager
async def _client() -> AsyncIterator[AsyncClient]:
    app = create_app(step_delay_seconds=0.005)
    async with (
        LifespanManager(app),
        AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
        ) as client,
    ):
        yield client


async def _wait_for_status(
    client: AsyncClient,
    environment_id: str,
    expected_status: str,
    *,
    timeout_seconds: float = 1.0,
) -> dict[str, object]:
    deadline = asyncio.get_running_loop().time() + timeout_seconds
    while asyncio.get_running_loop().time() < deadline:
        response = await client.get(f"/environments/{environment_id}")
        assert response.status_code == 200
        body = response.json()
        if body["status"] == expected_status:
            return body
        await asyncio.sleep(0.005)
    pytest.fail(f"Environment did not reach {expected_status} before the timeout")


@pytest.mark.anyio
async def test_lists_only_approved_applications() -> None:
    async with _client() as client:
        response = await client.get("/applications")

    assert response.status_code == 200
    assert response.json() == [
        {
            "applicationId": "hello-environment",
            "displayName": "Hello Environment",
            "sessionMinutes": 15,
            "maxLifetimeMinutes": 30,
        }
    ]


@pytest.mark.anyio
async def test_creation_is_async_and_eventually_becomes_ready() -> None:
    async with _client() as client:
        response = await client.post(
            "/environments",
            headers={"Idempotency-Key": "contract-create-001"},
            json={"applicationId": "hello-environment"},
        )

        assert response.status_code == 202
        assert response.headers["Idempotency-Replayed"] == "false"
        created = response.json()
        assert created["status"] == "REQUESTED"
        assert created["endpoint"] is None

        ready = await _wait_for_status(client, created["environmentId"], "READY")
        assert ready["readyAt"] is not None
        assert ready["endpoint"] == f"https://{created['environmentId']}.example.invalid"


@pytest.mark.anyio
async def test_duplicate_creation_replays_the_same_environment() -> None:
    async with _client() as client:
        request = {
            "headers": {"Idempotency-Key": "contract-duplicate-001"},
            "json": {"applicationId": "hello-environment"},
        }
        first = await client.post("/environments", **request)
        duplicate = await client.post("/environments", **request)

        assert first.status_code == duplicate.status_code == 202
        assert duplicate.headers["Idempotency-Replayed"] == "true"
        assert duplicate.json()["environmentId"] == first.json()["environmentId"]


@pytest.mark.anyio
async def test_termination_is_async_idempotent_and_eventually_destroyed() -> None:
    async with _client() as client:
        created = (
            await client.post(
                "/environments",
                headers={"Idempotency-Key": "contract-delete-001"},
                json={"applicationId": "hello-environment"},
            )
        ).json()
        environment_id = created["environmentId"]

        first = await client.delete(f"/environments/{environment_id}")
        duplicate = await client.delete(f"/environments/{environment_id}")

        assert first.status_code == duplicate.status_code == 202
        assert first.json()["status"] == duplicate.json()["status"] == "TERMINATING"
        destroyed = await _wait_for_status(client, environment_id, "DESTROYED")
        assert destroyed["destroyedAt"] is not None
        assert destroyed["endpoint"] is None


@pytest.mark.parametrize(
    ("headers", "body", "expected_status"),
    [
        ({}, {"applicationId": "hello-environment"}, 422),
        ({"Idempotency-Key": "   "}, {"applicationId": "hello-environment"}, 422),
        ({"Idempotency-Key": "unknown-app-001"}, {"applicationId": "unknown"}, 422),
    ],
)
@pytest.mark.anyio
async def test_creation_rejects_invalid_public_input(
    headers: dict[str, str],
    body: dict[str, str],
    expected_status: int,
) -> None:
    async with _client() as client:
        response = await client.post("/environments", headers=headers, json=body)

        assert response.status_code == expected_status


@pytest.mark.anyio
async def test_unknown_environment_returns_not_found() -> None:
    async with _client() as client:
        assert (await client.get("/environments/env-missing")).status_code == 404
        assert (await client.delete("/environments/env-missing")).status_code == 404


@pytest.mark.anyio
async def test_idempotency_key_cannot_be_reused_for_a_different_request() -> None:
    repository = InMemoryEnvironmentRepository()
    await repository.reserve(
        environment_id="env-first",
        application_id="first-application",
        idempotency_key="shared-key",
    )

    with pytest.raises(IdempotencyConflict, match="different request"):
        await repository.reserve(
            environment_id="env-second",
            application_id="second-application",
            idempotency_key="shared-key",
        )

    assert await repository.count() == 1
