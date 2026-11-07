"""Application service coordinating profiles, persistence, and lifecycle work."""

from collections.abc import Mapping
from uuid import uuid4

from ephemeral_environments.application_profiles import ApplicationProfile
from ephemeral_environments.environment import EnvironmentRecord
from ephemeral_environments.provisioner import FakeProvisioner
from ephemeral_environments.repository import InMemoryEnvironmentRepository, Reservation


class ApplicationNotApproved(ValueError):
    """Raised when public input does not match the approved catalog."""


class EnvironmentService:
    def __init__(
        self,
        *,
        catalog: Mapping[str, ApplicationProfile],
        repository: InMemoryEnvironmentRepository,
        provisioner: FakeProvisioner,
    ) -> None:
        self._catalog = catalog
        self._repository = repository
        self._provisioner = provisioner

    def list_applications(self) -> tuple[ApplicationProfile, ...]:
        return tuple(self._catalog.values())

    async def create_environment(
        self,
        *,
        application_id: str,
        idempotency_key: str,
    ) -> Reservation:
        if application_id not in self._catalog:
            raise ApplicationNotApproved(application_id)

        reservation = await self._repository.reserve(
            environment_id=f"env-{uuid4().hex[:12]}",
            application_id=application_id,
            idempotency_key=idempotency_key,
        )
        if reservation.created:
            await self._provisioner.provision(reservation.record.environment_id)
        return reservation

    async def get_environment(self, environment_id: str) -> EnvironmentRecord:
        return await self._repository.get(environment_id)

    async def terminate_environment(self, environment_id: str) -> EnvironmentRecord:
        record, started = await self._repository.request_termination(environment_id)
        if started:
            await self._provisioner.destroy(environment_id)
        return record
