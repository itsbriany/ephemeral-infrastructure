import pytest

from ephemeral_environments.naming import ResourceScope, mandatory_tags, resource_name


def test_ephemeral_name_and_tags_include_environment_identity() -> None:
    assert resource_name("service", environment_id="env-123") == (
        "ephemeral-environments-service-env-123"
    )
    assert mandatory_tags("service", ResourceScope.EPHEMERAL, environment_id="env-123") == {
        "platform": "ephemeral-environments",
        "component": "service",
        "resource-scope": "ephemeral",
        "managed-by": "aws-cdk",
        "cost-center": "ephemeral-environments",
        "environment-id": "env-123",
    }


def test_ephemeral_resource_requires_environment_id() -> None:
    with pytest.raises(ValueError, match="require an environment_id"):
        mandatory_tags("service", ResourceScope.EPHEMERAL)


def test_name_components_must_be_lowercase_kebab_case() -> None:
    with pytest.raises(ValueError, match="lowercase kebab-case"):
        resource_name("Bad_Component")
