"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All runtime configuration for the order service."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_primary_url: str
    database_replica_url: str

    # Service URLs
    cart_service_url: str = "http://cart-service:8002"
    product_service_url: str = "http://product-service:8001"
    payment_service_url: str = "http://payment-service:8005"
    notification_service_url: str = "http://notification-service:8006"

    # Security
    internal_service_secret: str
    jwt_public_key_url: str

    # Seller / invoice
    seller_gstin: str = "29ABCDE1234F1Z5"
    seller_address: str = "123 Silk Market, Bengaluru, Karnataka - 560001"

    # CORS
    frontend_origin: str = "http://localhost:3000"

    # Logging
    log_level: str = "INFO"

    # App
    app_env: str = "production"
    app_port: int = int(os.getenv("PORT", 8000))


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings singleton."""
    return Settings()  # type: ignore[call-arg]
