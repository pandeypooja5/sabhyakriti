"""AWS S3 adapter for generating presigned PUT URLs and deleting objects."""
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
    """Wraps boto3 S3 client for presigned URL generation and object deletion."""

    def __init__(self, bucket_name: str, region: str) -> None:
        self._bucket = bucket_name
        self._region = region
        self._client = boto3.client("s3", region_name=region)

    def generate_presigned_put_url(
        self,
        s3_key: str,
        ttl_seconds: int,
        content_type: str,
    ) -> str:
        """Generate a presigned S3 PUT URL for direct browser upload.

        Args:
            s3_key: The destination object key in S3.
            ttl_seconds: URL expiry time in seconds (max 900 for PUT).
            content_type: MIME type of the object being uploaded.

        Returns:
            Presigned URL string.

        Raises:
            ValueError: If content_type is not in the allowed set.
        """
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
            logger.debug("s3_presigned_url_generated", s3_key=s3_key, ttl=ttl_seconds)
            return url
        except ClientError as exc:
            logger.error("s3_presigned_url_error", s3_key=s3_key, error=str(exc))
            raise

    def delete_object(self, s3_key: str) -> None:
        """Delete an object from S3 (best-effort; errors are logged, not raised).

        Args:
            s3_key: The object key to delete.
        """
        try:
            self._client.delete_object(Bucket=self._bucket, Key=s3_key)
            logger.info("s3_object_deleted", s3_key=s3_key)
        except ClientError as exc:
            logger.error("s3_delete_error", s3_key=s3_key, error=str(exc))
