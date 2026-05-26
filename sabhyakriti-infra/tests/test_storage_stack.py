"""CDK assertion tests for StorageStack."""
from __future__ import annotations

import aws_cdk as cdk
import aws_cdk.assertions as assertions
import pytest

from sabhyakriti_infra.stacks.storage_stack import StorageStack


@pytest.fixture
def template() -> assertions.Template:
    app = cdk.App()
    stack = StorageStack(app, "TestStorage")
    return assertions.Template.from_stack(stack)


def test_s3_bucket_blocks_public_access(template: assertions.Template) -> None:
    template.has_resource_properties(
        "AWS::S3::Bucket",
        {
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "BlockPublicPolicy": True,
                "IgnorePublicAcls": True,
                "RestrictPublicBuckets": True,
            }
        },
    )


def test_s3_bucket_encrypted(template: assertions.Template) -> None:
    template.has_resource_properties(
        "AWS::S3::Bucket",
        {"BucketEncryption": assertions.Match.object_like({"ServerSideEncryptionConfiguration": assertions.Match.any_value()})},
    )


def test_cloudfront_distribution_created(template: assertions.Template) -> None:
    template.resource_count_is("AWS::CloudFront::Distribution", 1)


def test_cloudfront_enforces_https(template: assertions.Template) -> None:
    template.has_resource_properties(
        "AWS::CloudFront::Distribution",
        {
            "DistributionConfig": assertions.Match.object_like({
                "DefaultCacheBehavior": assertions.Match.object_like({
                    "ViewerProtocolPolicy": "redirect-to-https",
                })
            })
        },
    )
