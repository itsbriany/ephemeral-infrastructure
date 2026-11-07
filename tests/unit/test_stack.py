import os
from pathlib import Path

# Configure jsii before importing CDK so tests do not trust a shared, group-writable cache.
os.environ.setdefault(
    "JSII_RUNTIME_PACKAGE_CACHE_ROOT",
    str(Path(__file__).resolve().parents[2] / ".cache" / "jsii"),
)

import aws_cdk as cdk
from aws_cdk.assertions import Template

from ephemeral_environments.stacks.control_plane import ControlPlaneFoundationStack


def test_milestone_zero_stack_creates_no_aws_resources() -> None:
    app = cdk.App()
    stack = ControlPlaneFoundationStack(
        app,
        "TestControlPlane",
        env=cdk.Environment(region="ca-central-1"),
    )

    template = Template.from_stack(stack).to_json()

    assert template.get("Resources", {}) == {}
    assert template["Outputs"]["DeploymentRegion"]["Value"] == {"Ref": "AWS::Region"}
