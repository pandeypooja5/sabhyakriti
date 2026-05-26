"""CDK snapshot + assertion tests for NetworkStack."""
from __future__ import annotations

import aws_cdk as cdk
import aws_cdk.assertions as assertions
import pytest

from sabhyakriti_infra.config import SERVICES
from sabhyakriti_infra.stacks.network_stack import NetworkStack


@pytest.fixture
def template() -> assertions.Template:
    app = cdk.App()
    stack = NetworkStack(app, "TestNetwork")
    return assertions.Template.from_stack(stack)


def test_vpc_created_with_correct_cidr(template: assertions.Template) -> None:
    template.has_resource_properties(
        "AWS::EC2::VPC",
        {"CidrBlock": "10.0.0.0/16"},
    )


def test_one_nat_gateway(template: assertions.Template) -> None:
    template.resource_count_is("AWS::EC2::NatGateway", 1)


def test_security_group_created_for_each_service(template: assertions.Template) -> None:
    # NetworkStack creates ALB SG + RDS SG + Redis SG + one per service
    expected_min = len(SERVICES) + 3
    sgs = template.find_resources("AWS::EC2::SecurityGroup")
    assert len(sgs) >= expected_min


def test_alb_sg_allows_https_inbound(template: assertions.Template) -> None:
    template.has_resource_properties(
        "AWS::EC2::SecurityGroup",
        {
            "SecurityGroupIngress": assertions.Match.array_with([
                assertions.Match.object_like({"FromPort": 443, "ToPort": 443}),
            ])
        },
    )


def test_ssm_vpc_endpoints_created(template: assertions.Template) -> None:
    endpoints = template.find_resources("AWS::EC2::VPCEndpoint")
    # Expect at least SSM, SSMMessages, EC2Messages endpoints
    assert len(endpoints) >= 3
