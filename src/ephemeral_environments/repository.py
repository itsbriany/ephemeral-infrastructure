"""In-memory Milestone 1 persistence with atomic lifecycle updates."""

import asyncio
from dataclasses import dataclass
from datetime import datetime

from ephemeral_environments.environment import EnvironmentRecord
from ephemeral_environments.lifecycle import EnvironmentStatus, require_transition


class EnvironmentNotFound(LookupError):
    """Raised when an environment ID is not present in the registry."""


class IdempotencyConflict(ValueError):
    """Raised when a key is reused for a different creation request."""


@dataclass(frozen=True, slots=True)
class Reservation:
    record: EnvironmentRecord
    created: bool


class InMemoryEnvironmentRepository:
    """Process-local registry used to prove the API contract before AWS exists."""

    def __init__(self) -> None:
        self._records: dict[str, EnvironmentRecord] = {}
        self._idempotency_keys: dict[str, tuple[str, str]] = {}
        self._lock = asyncio.Lock()

    async def reserve(
        self,
        *,
        environment_id: str,
        application_id: str,
        idempotency_key: str,
        now: datetime | None = None,
    ) -> Reservation:
        """Atomically reserve one ID or replay the matching earlier request."""
        async with self._lock:
            existing = self._idempotency_keys.get(idempotency_key)
            if existing is not None:
                existing_application_id, existing_environment_id = existing
                if existing_application_id != application_id:
                    raise IdempotencyConflict(
                        "Idempotency-Key was already used for a different request"
                    )
                return Reservation(self._records[existing_environment_id], created=False)

            record = EnvironmentRecord.requested(
                environment_id=environment_id,
                application_id=application_id,
                now=now,
            )
            self._records[environment_id] = record
            self._idempotency_keys[idempotency_key] = (application_id, environment_id)
            return Reservation(record, created=True)

    async def get(self, environment_id: str) -> EnvironmentRecord:
        async with self._lock:
            try:
                return self._records[environment_id]
            except KeyError as error:
                raise EnvironmentNotFound(environment_id) from error

    async def transition_if_current(
        self,
        environment_id: str,
        *,
        current: EnvironmentStatus,
        target: EnvironmentStatus,
        endpoint: str | None = None,
        now: datetime | None = None,
    ) -> EnvironmentRecord | None:
        """Apply a transition only if another operation has not changed the state."""
        async with self._lock:
            record = self._record_for(environment_id)
            if record.status is not current:
                return None

            require_transition(record.status, target)
            updated = record.with_status(target, endpoint=endpoint, now=now)
            self._records[environment_id] = updated
            return updated

    async def request_termination(
        self,
        environment_id: str,
        *,
        now: datetime | None = None,
    ) -> tuple[EnvironmentRecord, bool]:
        """Atomically and idempotently move an active record to TERMINATING."""
        async with self._lock:
            record = self._record_for(environment_id)
            if record.status in {EnvironmentStatus.TERMINATING, EnvironmentStatus.DESTROYED}:
                return record, False

            require_transition(record.status, EnvironmentStatus.TERMINATING)
            updated = record.with_status(EnvironmentStatus.TERMINATING, now=now)
            self._records[environment_id] = updated
            return updated, True

    async def count(self) -> int:
        async with self._lock:
            return len(self._records)

    def _record_for(self, environment_id: str) -> EnvironmentRecord:
        try:
            return self._records[environment_id]
        except KeyError as error:
            raise EnvironmentNotFound(environment_id) from error
