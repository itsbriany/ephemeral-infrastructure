import pytest

from ephemeral_environments.application_profiles import (
    APPLICATION_CATALOG,
    HELLO_ENVIRONMENT,
    ApplicationProfile,
)


def test_catalog_contains_only_the_milestone_zero_sample_profile() -> None:
    assert APPLICATION_CATALOG == {"hello-environment": HELLO_ENVIRONMENT}
    assert HELLO_ENVIRONMENT.health_path == "/health"
    assert HELLO_ENVIRONMENT.max_lifetime_minutes > HELLO_ENVIRONMENT.session_minutes


def test_maximum_lifetime_cannot_be_shorter_than_session() -> None:
    with pytest.raises(ValueError, match="cannot be shorter"):
        ApplicationProfile(
            application_id="invalid-profile",
            display_name="Invalid",
            container_port=8080,
            health_path="/health",
            cpu_units=256,
            memory_mib=512,
            session_minutes=30,
            max_lifetime_minutes=15,
        )
