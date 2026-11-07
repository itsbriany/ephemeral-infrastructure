"""Provider-neutral environment lifecycle rules."""

from enum import StrEnum


class EnvironmentStatus(StrEnum):
    REQUESTED = "REQUESTED"
    PROVISIONING = "PROVISIONING"
    VERIFYING = "VERIFYING"
    READY = "READY"
    TERMINATING = "TERMINATING"
    DESTROYED = "DESTROYED"
    PROVISIONING_FAILED = "PROVISIONING_FAILED"
    CLEANUP_FAILED = "CLEANUP_FAILED"


ALLOWED_TRANSITIONS: dict[EnvironmentStatus, frozenset[EnvironmentStatus]] = {
    EnvironmentStatus.REQUESTED: frozenset(
        {
            EnvironmentStatus.PROVISIONING,
            EnvironmentStatus.PROVISIONING_FAILED,
            EnvironmentStatus.TERMINATING,
        }
    ),
    EnvironmentStatus.PROVISIONING: frozenset(
        {
            EnvironmentStatus.VERIFYING,
            EnvironmentStatus.PROVISIONING_FAILED,
            EnvironmentStatus.TERMINATING,
        }
    ),
    EnvironmentStatus.VERIFYING: frozenset(
        {
            EnvironmentStatus.READY,
            EnvironmentStatus.PROVISIONING_FAILED,
            EnvironmentStatus.TERMINATING,
        }
    ),
    EnvironmentStatus.READY: frozenset({EnvironmentStatus.TERMINATING}),
    EnvironmentStatus.PROVISIONING_FAILED: frozenset({EnvironmentStatus.TERMINATING}),
    EnvironmentStatus.TERMINATING: frozenset(
        {EnvironmentStatus.DESTROYED, EnvironmentStatus.CLEANUP_FAILED}
    ),
    EnvironmentStatus.CLEANUP_FAILED: frozenset({EnvironmentStatus.TERMINATING}),
    EnvironmentStatus.DESTROYED: frozenset(),
}


class InvalidLifecycleTransition(ValueError):
    """Raised when a caller attempts an unsupported lifecycle transition."""


def can_transition(current: EnvironmentStatus, target: EnvironmentStatus) -> bool:
    """Return whether the lifecycle permits moving from current to target."""
    return target in ALLOWED_TRANSITIONS[current]


def require_transition(current: EnvironmentStatus, target: EnvironmentStatus) -> None:
    """Reject invalid transitions with an operator-friendly error."""
    if not can_transition(current, target):
        raise InvalidLifecycleTransition(
            f"Cannot transition environment from {current} to {target}"
        )
