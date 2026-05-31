"""S3-compatible adapter — works with AWS S3 and Cloudflare R2."""
from __future__ import annotations

import structlog
import boto3
from botocore.exceptions import ClientError

logger = structlog.get_logger(__name__)

_ALLOWED_CONTENT_TYPES = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
    }
)


class AWSS3Adapter:
    """Wraps boto3 S3 client for presigned URL generation and object deletion.

    Compatible with AWS S3 and any S3-compatible service (e.g. Cloudflare R2).
    Pass ``endpoint_url`` to point at R2:
        https://<account_id>.r2.cloudflarestorage.com
    """

    def __init__(
        self,
        bucket_name: str,
        region: str,
        endpoint_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
    ) -> None:
        self._bucket = bucket_name
        self._region = region
        self._endpoint_url = endpoint_url

        kwargs: dict = {"region_name": region}
        if endpoint_url:
            kwargs["endpoint_url"] = endpoint_url
        if access_key_id and secret_access_key:
            kwargs["aws_access_key_id"] = access_key_id
            kwargs["aws_secret_access_key"] = secret_access_key

        self._client = boto3.client("s3", **kwargs)

    def generate_presigned_put_url(
        self,
        s3_key: str,
        ttl_seconds: int,
        content_type: str,
    ) -> str:
        """Generate a presigned PUT URL for direct browser upload."""
        if content_type not in _ALLOWED_CONTENT_TYPES:
            raise ValueError(
                f"Content-Type '{content_type}' is not allowed. "
                f"Allowed types: {sorted(_ALLOWED_CONTENT_TYPES)}"
            )

        try:
            url: str = self._client.generate_presigned_url(
                ClientMethod="put_object",
                Params={
                    "Bucket": self._bucket,
                    "Key": s3_key,
                    "ContentType": content_type,
                },
                ExpiresIn=ttl_seconds,
            )
            logger.debug("presigned_url_generated", s3_key=s3_key, ttl=ttl_seconds)
            return url
        except ClientError as exc:
            logger.error("presigned_url_error", s3_key=s3_key, error=str(exc))
            raise

    def upload_fileobj(self, fileobj, s3_key: str, content_type: str) -> None:
        """Upload a file-like object directly (used in server-side uploads)."""
        try:
            self._client.upload_fileobj(
                fileobj,
                self._bucket,
                s3_key,
                ExtraArgs={"ContentType": content_type},
            )
            logger.info("s3_upload_complete", s3_key=s3_key)
        except ClientError as exc:
            logger.error("s3_upload_error", s3_key=s3_key, error=str(exc))
            raise

    def delete_object(self, s3_key: str) -> None:
        """Delete an object (best-effort; errors are logged, not raised)."""
        try:
            self._client.delete_object(Bucket=self._bucket, Key=s3_key)
            logger.info("s3_object_deleted", s3_key=s3_key)
        except ClientError as exc:
            logger.error("s3_delete_error", s3_key=s3_key, error=str(exc))
