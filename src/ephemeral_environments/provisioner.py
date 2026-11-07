"""Small in-process provisioner that simulates a remote asynchronous workflow."""

import asyncio
from dataclasses import dataclass
from enum import StrEnum

from ephemeral_environments.lifecycle import EnvironmentStatus
from ephemeral_environments.repository import InMemoryEnvironmentRepository


class WorkType(StrEnum):
    PROVISION = "PROVISION"
    DESTROY = "DESTROY"


@dataclass(frozen=True, slots=True)
class WorkItem:
    work_type: WorkType
    environment_id: str


class FakeProvisioner:
    """Drive valid lifecycle transitions without creating infrastructure."""

    def __init__(
        self,
        repository: InMemoryEnvironmentRepository,
        *,
        step_delay_seconds: float = 0.05,
    ) -> None:
        self._repository = repository
        self._step_delay_seconds = step_delay_seconds
        self._queue: asyncio.Queue[WorkItem | None] = asyncio.Queue()
        self._worker: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if self._worker is None:
            self._worker = asyncio.create_task(self._run(), name="fake-provisioner")

    async def stop(self) -> None:
        if self._worker is None:
            return
        await self._queue.join()
        await self._queue.put(None)
        await self._worker
        self._worker = None

    async def provision(self, environment_id: str) -> None:
        await self._queue.put(WorkItem(WorkType.PROVISION, environment_id))

    async def destroy(self, environment_id: str) -> None:
        await self._queue.put(WorkItem(WorkType.DESTROY, environment_id))

    async def _run(self) -> None:
        while True:
            item = await self._queue.get()
            try:
                if item is None:
                    return
                if item.work_type is WorkType.PROVISION:
                    await self._simulate_provisioning(item.environment_id)
                else:
                    await self._simulate_destruction(item.environment_id)
            finally:
                self._queue.task_done()

    async def _simulate_provisioning(self, environment_id: str) -> None:
        if not await self._advance(
            environment_id,
            current=EnvironmentStatus.REQUESTED,
            target=EnvironmentStatus.PROVISIONING,
        ):
            return
        if not await self._advance(
            environment_id,
            current=EnvironmentStatus.PROVISIONING,
            target=EnvironmentStatus.VERIFYING,
        ):
            return

        await asyncio.sleep(self._step_delay_seconds)
        await self._repository.transition_if_current(
            environment_id,
            current=EnvironmentStatus.VERIFYING,
            target=EnvironmentStatus.READY,
            endpoint=f"https://{environment_id}.example.invalid",
        )

    async def _simulate_destruction(self, environment_id: str) -> None:
        await asyncio.sleep(self._step_delay_seconds)
        await self._repository.transition_if_current(
            environment_id,
            current=EnvironmentStatus.TERMINATING,
            target=EnvironmentStatus.DESTROYED,
        )

    async def _advance(
        self,
        environment_id: str,
        *,
        current: EnvironmentStatus,
        target: EnvironmentStatus,
    ) -> bool:
        await asyncio.sleep(self._step_delay_seconds)
        updated = await self._repository.transition_if_current(
            environment_id,
            current=current,
            target=target,
        )
        return updated is not None
