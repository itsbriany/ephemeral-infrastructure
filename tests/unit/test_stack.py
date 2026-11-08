import os
from pathlib import Path
from typing import Any

# Configure jsii before importing CDK so tests do not trust a shared, group-writable cache.
os.environ.setdefault(
    "JSII_RUNTIME_PACKAGE_CACHE_ROOT",
    str(Path(__file__).resolve().parents[2] / ".cache" / "jsii"),
)

import aws_cdk as cdk
from aws_cdk.assertions import Template

from ephemeral_environments.stacks.control_plane import ControlPlaneStack


def _template() -> dict[str, Any]:
    app = cdk.App()
    stack = ControlPlaneStack(
        app,
        "TestControlPlane",
        env=cdk.Environment(region="ca-central-1"),
    )
    return Template.from_stack(stack).to_json()


def _actions(statement: dict[str, Any]) -> set[str]:
    value = statement["Action"]
    return set(value if isinstance(value, list) else [value])


def test_stack_creates_only_milestone_2_control_plane_resources() -> None:
    resources = _template()["Resources"]
    resource_types = [resource["Type"] for resource in resources.values()]

    assert resource_types.count("AWS::DynamoDB::Table") == 1
    assert resource_types.count("AWS::Lambda::Function") == 4
    assert resource_types.count("AWS::ApiGatewayV2::Api") == 1
    assert resource_types.count("AWS::ApiGatewayV2::Route") == 4
    assert resource_types.count("AWS::ApiGatewayV2::Stage") == 1
    assert resource_types.count("AWS::Logs::LogGroup") == 5
    assert not any(resource_type.startswith("AWS::ECS::") for resource_type in resource_types)
    assert "AWS::StepFunctions::StateMachine" not in resource_types


def test_registry_is_on_demand_recoverable_encrypted_and_retained() -> None:
    table = next(
        resource
        for resource in _template()["Resources"].values()
        if resource["Type"] == "AWS::DynamoDB::Table"
    )

    assert table["DeletionPolicy"] == "Retain"
    assert table["UpdateReplacePolicy"] == "Retain"
    properties = table["Properties"]
    assert properties["BillingMode"] == "PAY_PER_REQUEST"
    assert properties["KeySchema"] == [{"AttributeName": "pk", "KeyType": "HASH"}]
    assert properties["SSESpecification"] == {"SSEEnabled": True}
    assert properties["PointInTimeRecoverySpecification"] == {
        "PointInTimeRecoveryEnabled": True,
        "RecoveryPeriodInDays": 7,
    }


def test_http_api_exposes_only_the_four_milestone_routes() -> None:
    template = _template()
    routes = {
        resource["Properties"]["RouteKey"]
        for resource in template["Resources"].values()
        if resource["Type"] == "AWS::ApiGatewayV2::Route"
    }
    stage = next(
        resource
        for resource in template["Resources"].values()
        if resource["Type"] == "AWS::ApiGatewayV2::Stage"
    )

    assert routes == {
        "GET /applications",
        "POST /environments",
        "GET /environments/{environmentId}",
        "DELETE /environments/{environmentId}",
    }
    assert stage["Properties"]["DefaultRouteSettings"] == {
        "ThrottlingBurstLimit": 20,
        "ThrottlingRateLimit": 10,
    }
    assert "DestinationArn" in stage["Properties"]["AccessLogSettings"]
    assert "sourceIp" not in stage["Properties"]["AccessLogSettings"]["Format"]


def test_each_lambda_role_has_only_its_required_table_actions() -> None:
    resources = _template()["Resources"]
    roles = [resource for resource in resources.values() if resource["Type"] == "AWS::IAM::Role"]
    policies = [
        resource["Properties"]["PolicyDocument"]["Statement"]
        for resource in resources.values()
        if resource["Type"] == "AWS::IAM::Policy"
    ]
    table_action_sets = {
        frozenset(
            action
            for statement in statements
            for action in _actions(statement)
            if action.startswith("dynamodb:")
        )
        for statements in policies
    }

    assert len(roles) == 4
    assert all("ManagedPolicyArns" not in role["Properties"] for role in roles)
    assert table_action_sets == {
        frozenset(),
        frozenset({"dynamodb:GetItem", "dynamodb:TransactWriteItems"}),
        frozenset({"dynamodb:GetItem"}),
        frozenset({"dynamodb:GetItem", "dynamodb:UpdateItem"}),
    }
    for statements in policies:
        for statement in statements:
            assert statement["Resource"] != "*"


def test_all_control_plane_log_groups_retain_logs_for_30_days() -> None:
    log_groups = [
        resource
        for resource in _template()["Resources"].values()
        if resource["Type"] == "AWS::Logs::LogGroup"
    ]

    assert len(log_groups) == 5
    assert all(log_group["Properties"]["RetentionInDays"] == 30 for log_group in log_groups)
