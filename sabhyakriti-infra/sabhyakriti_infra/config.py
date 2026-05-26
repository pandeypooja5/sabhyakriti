from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ServiceConfig:
    name: str          # e.g. "auth-service"
    port: int          # container port
    ec2_type: str      # e.g. "t3.medium"
    alb_paths: list[str] = field(default_factory=list)  # public ALB path patterns
    is_internal_only: bool = False  # True = no public ALB routing


SERVICES: list[ServiceConfig] = [
    ServiceConfig(
        name="auth-service", port=8001, ec2_type="t3.medium",
        alb_paths=["/api/v1/auth/*", "/auth/.well-known/*", "/health"],
    ),
    ServiceConfig(
        name="product-service", port=8002, ec2_type="t3.large",
        alb_paths=[
            "/api/v1/products/*", "/api/v1/categories/*",
            "/api/v1/reviews/*", "/api/v1/media/*",
        ],
    ),
    ServiceConfig(
        name="cart-service", port=8003, ec2_type="t3.medium",
        alb_paths=["/api/v1/cart/*", "/api/v1/wishlist/*"],
    ),
    ServiceConfig(
        name="order-service", port=8004, ec2_type="t3.medium",
        alb_paths=["/api/v1/orders/*", "/api/v1/addresses/*"],
    ),
    ServiceConfig(
        name="payment-service", port=8005, ec2_type="t3.medium",
        alb_paths=["/api/v1/payments/*"],
    ),
    ServiceConfig(
        name="notification-service", port=8006, ec2_type="t3.small",
        is_internal_only=True,  # only reachable within VPC
    ),
    ServiceConfig(
        name="admin-service", port=8007, ec2_type="t3.small",
        alb_paths=["/api/v1/admin/*"],
    ),
]

# Infrastructure constants
VPC_CIDR = "10.0.0.0/16"
AWS_REGION = "ap-south-1"
AWS_ACCOUNT = ""  # set via CDK_DEFAULT_ACCOUNT env var
DOMAIN_NAME = "sabhyakriti.com"
API_SUBDOMAIN = f"api.{DOMAIN_NAME}"
CDN_SUBDOMAIN = f"cdn.{DOMAIN_NAME}"
DB_NAME = "sabhyakriti"
DB_PORT = 5432
REDIS_PORT = 6379
LOG_RETENTION_DAYS = 90
LOW_STOCK_THRESHOLD = 5
