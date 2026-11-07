"""Provider-neutral environment records exposed by the lifecycle API."""

from dataclasses import dataclass, replace
from datetime import UTC, datetime

from ephemeral_environments.lifecycle import EnvironmentStatus


@dataclass(frozen=True, slots=True)
class EnvironmentRecord:
    """An immutable snapshot of one requested environment."""

    environment_id: str
    application_id: str
    status: EnvironmentStatus
    created_at: datetime
    updated_at: datetime
    ready_at: datetime | None = None
    destroyed_at: datetime | None = None
    endpoint: str | None = None

    @classmethod
    def requested(
        cls,
        *,
        environment_id: str,
        application_id: str,
        now: datetime | None = None,
    ) -> "EnvironmentRecord":
        timestamp = now or datetime.now(UTC)
        return cls(
            environment_id=environment_id,
            application_id=application_id,
            status=EnvironmentStatus.REQUESTED,
            created_at=timestamp,
            updated_at=timestamp,
        )

    def with_status(
        self,
        status: EnvironmentStatus,
        *,
        now: datetime | None = None,
        endpoint: str | None = None,
    ) -> "EnvironmentRecord":
        """Return a new snapshot after a validated repository transition."""
        timestamp = now or datetime.now(UTC)
        ready_at = timestamp if status is EnvironmentStatus.READY else self.ready_at
        destroyed_at = timestamp if status is EnvironmentStatus.DESTROYED else self.destroyed_at

        if status in {EnvironmentStatus.TERMINATING, EnvironmentStatus.DESTROYED}:
            endpoint = None
        elif endpoint is None:
            endpoint = self.endpoint

        return replace(
            self,
            status=status,
            updated_at=timestamp,
            ready_at=ready_at,
            destroyed_at=destroyed_at,
            endpoint=endpoint,
        )
