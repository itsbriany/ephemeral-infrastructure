from aws_cdk import Aws, CfnOutput, Stack
from constructs import Construct


class ControlPlaneFoundationStack(Stack):
    """Milestone 0 stack boundary; resources arrive in later milestones."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs: object) -> None:
        super().__init__(scope, construct_id, **kwargs)

        CfnOutput(
            self,
            "DeploymentRegion",
            value=Aws.REGION,
            description="Regional workload and control-plane deployment region.",
        )
