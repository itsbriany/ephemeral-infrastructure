"""Names and mandatory cost/ownership tags shared by future stacks."""

import re
from enum import StrEnum

from ephemeral_environments.config import PLATFORM_ID

_NAME_COMPONENT = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ResourceScope(StrEnum):
    PERSISTENT = "persistent"
    SHARED = "shared"
    EPHEMERAL = "ephemeral"


def resource_name(component: str, *, environment_id: str | None = None) -> str:
    """Build a predictable resource name from validated components."""
    for value, label in ((component, "component"), (environment_id, "environment_id")):
        if value is not None and not _NAME_COMPONENT.fullmatch(value):
            raise ValueError(f"{label} must use lowercase kebab-case")

    parts = [PLATFORM_ID, component]
    if environment_id is not None:
        parts.append(environment_id)
    return "-".join(parts)


def mandatory_tags(
    component: str,
    scope: ResourceScope,
    *,
    environment_id: str | None = None,
) -> dict[str, str]:
    """Return the tags required for ownership, cleanup, and cost attribution."""
    if scope is ResourceScope.EPHEMERAL and environment_id is None:
        raise ValueError("Ephemeral resources require an environment_id tag")
    if scope is not ResourceScope.EPHEMERAL and environment_id is not None:
        raise ValueError("Only ephemeral resources may carry an environment_id tag")
    resource_name(component, environment_id=environment_id)

    tags = {
        "platform": PLATFORM_ID,
        "component": component,
        "resource-scope": scope.value,
        "managed-by": "aws-cdk",
        "cost-center": PLATFORM_ID,
    }
    if environment_id is not None:
        tags["environment-id"] = environment_id
    return tags
