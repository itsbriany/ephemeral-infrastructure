from pathlib import Path

from aws_cdk import Aws, CfnOutput, Duration, RemovalPolicy, Stack, Tags
from aws_cdk import aws_apigateway as apigateway
from aws_cdk import aws_apigatewayv2 as apigatewayv2
from aws_cdk import aws_apigatewayv2_integrations as integrations
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_iam as iam
from aws_cdk import aws_lambda as lambda_
from aws_cdk import aws_logs as logs
from constructs import Construct

from ephemeral_environments.naming import ResourceScope, mandatory_tags, resource_name


class ControlPlaneStack(Stack):
    """Persistent Milestone 2 registry and HTTP API; no workload resources."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs: object) -> None:
        super().__init__(scope, construct_id, **kwargs)

        registry = dynamodb.Table(
            self,
            "EnvironmentRegistry",
            table_name=resource_name("registry"),
            partition_key=dynamodb.Attribute(
                name="pk",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            encryption=dynamodb.TableEncryption.AWS_MANAGED,
            point_in_time_recovery_specification=dynamodb.PointInTimeRecoverySpecification(
                point_in_time_recovery_enabled=True,
                recovery_period_in_days=7,
            ),
            removal_policy=RemovalPolicy.RETAIN,
        )
        self._tag(registry, "registry")

        source_directory = Path(__file__).resolve().parents[2]
        list_function = self._function(
            "ListApplications",
            component="api-list-applications",
            handler="ephemeral_environments.aws_api.list_applications",
            source_directory=source_directory,
        )
        create_function = self._function(
            "CreateEnvironment",
            component="api-create-environment",
            handler="ephemeral_environments.aws_api.create_environment",
            source_directory=source_directory,
            table=registry,
            table_actions=("dynamodb:GetItem", "dynamodb:TransactWriteItems"),
        )
        get_function = self._function(
            "GetEnvironment",
            component="api-get-environment",
            handler="ephemeral_environments.aws_api.get_environment",
            source_directory=source_directory,
            table=registry,
            table_actions=("dynamodb:GetItem",),
        )
        terminate_function = self._function(
            "TerminateEnvironment",
            component="api-terminate-environment",
            handler="ephemeral_environments.aws_api.terminate_environment",
            source_directory=source_directory,
            table=registry,
            table_actions=("dynamodb:GetItem", "dynamodb:UpdateItem"),
        )

        api = apigatewayv2.HttpApi(
            self,
            "ControlPlaneApi",
            api_name=resource_name("api"),
            create_default_stage=False,
            description="Persistent lifecycle registry API; workload provisioning is not enabled.",
        )
        self._tag(api, "api")
        api.add_routes(
            path="/applications",
            methods=[apigatewayv2.HttpMethod.GET],
            integration=integrations.HttpLambdaIntegration(
                "ListApplicationsIntegration",
                list_function,
            ),
        )
        api.add_routes(
            path="/environments",
            methods=[apigatewayv2.HttpMethod.POST],
            integration=integrations.HttpLambdaIntegration(
                "CreateEnvironmentIntegration",
                create_function,
            ),
        )
        api.add_routes(
            path="/environments/{environmentId}",
            methods=[apigatewayv2.HttpMethod.GET],
            integration=integrations.HttpLambdaIntegration(
                "GetEnvironmentIntegration",
                get_function,
            ),
        )
        api.add_routes(
            path="/environments/{environmentId}",
            methods=[apigatewayv2.HttpMethod.DELETE],
            integration=integrations.HttpLambdaIntegration(
                "TerminateEnvironmentIntegration",
                terminate_function,
            ),
        )

        access_logs = logs.LogGroup(
            self,
            "ApiAccessLogs",
            log_group_name=f"/aws/apigateway/{resource_name('api')}",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY,
        )
        self._tag(access_logs, "api-access-logs")
        stage = apigatewayv2.HttpStage(
            self,
            "DefaultStage",
            http_api=api,
            stage_name="$default",
            auto_deploy=True,
            throttle=apigatewayv2.ThrottleSettings(
                burst_limit=20,
                rate_limit=10,
            ),
        )
        access_log_destination = apigatewayv2.LogGroupLogDestination(access_logs).bind(stage)
        cfn_stage = stage.node.default_child
        if not isinstance(cfn_stage, apigatewayv2.CfnStage):
            raise TypeError("HTTP stage did not produce the expected CloudFormation resource")
        cfn_stage.access_log_settings = apigatewayv2.CfnStage.AccessLogSettingsProperty(
            destination_arn=access_log_destination.destination_arn,
            format=apigateway.AccessLogFormat.custom(
                '{"requestId":"$context.requestId",'
                '"routeKey":"$context.routeKey",'
                '"status":"$context.status",'
                '"integrationStatus":"$context.integration.status",'
                '"responseLength":"$context.responseLength"}'
            ).to_string(),
        )

        CfnOutput(
            self,
            "DeploymentRegion",
            value=Aws.REGION,
            description="Regional workload and control-plane deployment region.",
        )
        CfnOutput(
            self,
            "ApiEndpoint",
            value=api.api_endpoint,
            description="Base URL for the persistent control-plane HTTP API.",
        )
        CfnOutput(
            self,
            "EnvironmentRegistryTableName",
            value=registry.table_name,
            description="DynamoDB table that owns environment and idempotency records.",
        )

    def _function(
        self,
        construct_id: str,
        *,
        component: str,
        handler: str,
        source_directory: Path,
        table: dynamodb.ITable | None = None,
        table_actions: tuple[str, ...] = (),
    ) -> lambda_.Function:
        function_name = resource_name(component)
        log_group = logs.LogGroup(
            self,
            f"{construct_id}Logs",
            log_group_name=f"/aws/lambda/{function_name}",
            retention=logs.RetentionDays.ONE_MONTH,
            removal_policy=RemovalPolicy.DESTROY,
        )
        self._tag(log_group, f"{component}-logs")

        role = iam.Role(
            self,
            f"{construct_id}Role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description=f"Least-privilege execution role for {function_name}.",
        )
        role.add_to_policy(
            iam.PolicyStatement(
                actions=["logs:CreateLogStream", "logs:PutLogEvents"],
                resources=[f"{log_group.log_group_arn}:*"],
            )
        )
        if table is not None and table_actions:
            role.add_to_policy(
                iam.PolicyStatement(
                    actions=list(table_actions),
                    resources=[table.table_arn],
                )
            )
        self._tag(role, f"{component}-role")

        function = lambda_.Function(
            self,
            construct_id,
            function_name=function_name,
            runtime=lambda_.Runtime.PYTHON_3_12,
            architecture=lambda_.Architecture.ARM_64,
            code=lambda_.Code.from_asset(
                str(source_directory),
                exclude=["**/__pycache__/**", "**/*.pyc"],
            ),
            handler=handler,
            description="Milestone 2 persistent control-plane API operation.",
            memory_size=256,
            timeout=Duration.seconds(10),
            environment=(
                {"ENVIRONMENTS_TABLE_NAME": table.table_name} if table is not None else None
            ),
            role=role,
            log_group=log_group,
            logging_format=lambda_.LoggingFormat.JSON,
            application_log_level_v2=lambda_.ApplicationLogLevel.INFO,
            system_log_level_v2=lambda_.SystemLogLevel.WARN,
        )
        self._tag(function, component)
        return function

    @staticmethod
    def _tag(construct: Construct, component: str) -> None:
        for key, value in mandatory_tags(component, ResourceScope.PERSISTENT).items():
            Tags.of(construct).add(key, value)
