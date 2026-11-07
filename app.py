#!/usr/bin/env python3

import os
from pathlib import Path

# Keep jsii's extracted runtime packages in a project-owned directory. Some shared developer
# machines intentionally reject a group-writable global cache as unsafe.
os.environ.setdefault(
    "JSII_RUNTIME_PACKAGE_CACHE_ROOT",
    str(Path(__file__).resolve().parent / ".cache" / "jsii"),
)

import aws_cdk as cdk

from ephemeral_environments.config import CONTROL_PLANE_STACK_NAME, DEFAULT_AWS_REGION
from ephemeral_environments.stacks.control_plane import ControlPlaneFoundationStack


def build_app() -> cdk.App:
    """Build the Milestone 0 cloud assembly without deploying it."""
    app = cdk.App(outdir="cdk.out")
    region = app.node.try_get_context("deploymentRegion") or DEFAULT_AWS_REGION
    environment = cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"),
        region=region,
    )

    ControlPlaneFoundationStack(
        app,
        CONTROL_PLANE_STACK_NAME,
        env=environment,
        description=(
            "Persistent control-plane foundation for the Ephemeral Environments platform. "
            "Milestone 0 intentionally creates no AWS resources."
        ),
    )
    return app


if __name__ == "__main__":
    build_app().synth()
