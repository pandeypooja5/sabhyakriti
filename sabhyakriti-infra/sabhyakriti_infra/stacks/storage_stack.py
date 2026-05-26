from __future__ import annotations

import aws_cdk as cdk
import aws_cdk.aws_cloudfront as cloudfront
import aws_cdk.aws_cloudfront_origins as origins
import aws_cdk.aws_s3 as s3
import aws_cdk.aws_ses as ses
import aws_cdk.aws_sns as sns
from constructs import Construct

from sabhyakriti_infra.config import CDN_SUBDOMAIN, DOMAIN_NAME


class StorageStack(cdk.Stack):
    """S3 product images + CloudFront CDN + SES email + SNS SMS."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs: object) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ── S3: Product Images ───────────────────────────────────────────────
        self.images_bucket = s3.Bucket(
            self, "ProductImagesBucket",
            bucket_name="sabhyakriti-product-images",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,  # SECURITY-09
            encryption=s3.BucketEncryption.S3_MANAGED,           # SECURITY-01
            enforce_ssl=True,
            versioned=False,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteIncompleteMultipart",
                    abort_incomplete_multipart_upload_after=cdk.Duration.days(1),
                )
            ],
            cors=[
                s3.CorsRule(
                    allowed_methods=[s3.HttpMethods.PUT],
                    allowed_origins=["https://sabhyakriti.com", "https://www.sabhyakriti.com"],
                    allowed_headers=["*"],
                    max_age=3000,
                )
            ],
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )

        # ── S3: ALB Access Logs ──────────────────────────────────────────────
        self.alb_logs_bucket = s3.Bucket(
            self, "AlbLogsBucket",
            bucket_name="sabhyakriti-alb-logs",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="ExpireLogs",
                    expiration=cdk.Duration.days(90),
                )
            ],
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )

        # ── CloudFront: Origin Access Control ────────────────────────────────
        oac = cloudfront.S3OriginAccessControl(
            self, "ProductImagesOac",
            description="OAC for Sabhyakriti product images",
        )

        # ── CloudFront Distribution ───────────────────────────────────────────
        self.distribution = cloudfront.Distribution(
            self, "ProductImagesDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3BucketOrigin.with_origin_access_control(
                    self.images_bucket,
                    origin_access_control=oac,
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                compress=True,
            ),
            domain_names=[CDN_SUBDOMAIN],
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,  # NA + Europe + Asia
            http_version=cloudfront.HttpVersion.HTTP2_AND_3,
            enable_logging=True,
            log_bucket=self.alb_logs_bucket,
            log_file_prefix="cloudfront/",
        )

        # Grant CloudFront read access to S3 (via OAC bucket policy)
        self.images_bucket.add_to_resource_policy(
            cdk.aws_iam.PolicyStatement(
                actions=["s3:GetObject"],
                principals=[cdk.aws_iam.ServicePrincipal("cloudfront.amazonaws.com")],
                resources=[self.images_bucket.arn_for_objects("*")],
                conditions={
                    "StringEquals": {
                        "aws:SourceArn": f"arn:aws:cloudfront::{self.account}:distribution/{self.distribution.distribution_id}"
                    }
                },
            )
        )

        # ── SES: Email Identity ───────────────────────────────────────────────
        # Domain identity — DKIM and MAIL FROM configured post-deploy in SES console
        self.ses_identity = ses.EmailIdentity(
            self, "SesEmailIdentity",
            identity=ses.Identity.domain(DOMAIN_NAME),
        )

        # ── SNS: SMS Topic (fallback for Twilio) ─────────────────────────────
        self.sms_topic = sns.Topic(
            self, "SmsTopic",
            topic_name="sabhyakriti-sms-fallback",
            display_name="Sabhyakriti SMS Fallback",
        )

        # ── Outputs ───────────────────────────────────────────────────────────
        cdk.CfnOutput(self, "ImagesBucketName", value=self.images_bucket.bucket_name)
        cdk.CfnOutput(self, "CloudFrontDomain", value=self.distribution.distribution_domain_name)
        cdk.CfnOutput(self, "CloudFrontId", value=self.distribution.distribution_id)
