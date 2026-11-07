import pytest

from ephemeral_environments.lifecycle import (
    EnvironmentStatus,
    InvalidLifecycleTransition,
    can_transition,
    require_transition,
)


@pytest.mark.parametrize(
    ("current", "target"),
    [
        (EnvironmentStatus.REQUESTED, EnvironmentStatus.PROVISIONING),
        (EnvironmentStatus.PROVISIONING, EnvironmentStatus.VERIFYING),
        (EnvironmentStatus.VERIFYING, EnvironmentStatus.READY),
        (EnvironmentStatus.READY, EnvironmentStatus.TERMINATING),
        (EnvironmentStatus.TERMINATING, EnvironmentStatus.DESTROYED),
        (EnvironmentStatus.CLEANUP_FAILED, EnvironmentStatus.TERMINATING),
    ],
)
def test_expected_transition_is_allowed(
    current: EnvironmentStatus, target: EnvironmentStatus
) -> None:
    assert can_transition(current, target)
    require_transition(current, target)


def test_destroyed_environment_is_terminal() -> None:
    for target in EnvironmentStatus:
        assert not can_transition(EnvironmentStatus.DESTROYED, target)


def test_invalid_transition_is_rejected() -> None:
    with pytest.raises(
        InvalidLifecycleTransition,
        match="Cannot transition environment from READY to PROVISIONING",
    ):
        require_transition(EnvironmentStatus.READY, EnvironmentStatus.PROVISIONING)
