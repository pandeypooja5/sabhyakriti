"""AWS CloudFront adapter for building CDN URLs."""
from __future__ import annotations


def build_cdn_url(s3_key: str, cloudfront_domain: str) -> str:
    """Build a CloudFront CDN URL from an S3 key.

    Args:
        s3_key: The S3 object key (e.g. ``products/uuid/image.jpg``).
        cloudfront_domain: The CloudFront distribution domain
            (e.g. ``d1234abc.cloudfront.net``).

    Returns:
        Full HTTPS URL for the CDN resource.
    """
    domain = cloudfront_domain.rstrip("/")
    key = s3_key.lstrip("/")
    # Use http for local development to avoid browser SSL errors
    scheme = "http" if domain.startswith("localhost") else "https"
    return f"{scheme}://{domain}/{key}"
