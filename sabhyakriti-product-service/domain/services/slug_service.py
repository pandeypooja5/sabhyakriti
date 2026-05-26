"""Domain slug generation service."""
from __future__ import annotations

import uuid

from slugify import slugify  # type: ignore[import-untyped]

_MAX_SLUG_LENGTH = 212
_SUFFIX_LENGTH = 8


def generate_slug(name: str) -> str:
    """Generate a URL-safe slug from a product name.

    The slug is lowercased, unicode-normalised, and limited to 212 chars to
    leave room for an 8-char UUID suffix if a collision is detected later.

    Args:
        name: Human-readable product name (may contain unicode characters).

    Returns:
        URL-safe slug string, at most 212 characters long.
    """
    raw = slugify(name, allow_unicode=False, max_length=_MAX_SLUG_LENGTH)
    if not raw:
        # Fallback for names that produce an empty slug (e.g. pure emoji)
        raw = "product"
    return raw


def make_unique_slug(base_slug: str, existing_slugs: set[str]) -> str:
    """Return a slug that is not already present in *existing_slugs*.

    If *base_slug* is already unique it is returned as-is. Otherwise a
    8-character UUID hex suffix is appended (with a leading hyphen) and the
    combined string is truncated to ``_MAX_SLUG_LENGTH + _SUFFIX_LENGTH + 1``
    characters.

    Args:
        base_slug: The desired slug (output of :func:`generate_slug`).
        existing_slugs: Set of slugs already in use.

    Returns:
        A slug that is guaranteed not to be in *existing_slugs*.
    """
    if base_slug not in existing_slugs:
        return base_slug

    # Trim base to leave room for "-xxxxxxxx"
    trimmed = base_slug[:_MAX_SLUG_LENGTH]
    suffix = uuid.uuid4().hex[:_SUFFIX_LENGTH]
    candidate = f"{trimmed}-{suffix}"

    # Extremely unlikely, but guard against suffix collision too
    while candidate in existing_slugs:
        suffix = uuid.uuid4().hex[:_SUFFIX_LENGTH]
        candidate = f"{trimmed}-{suffix}"

    return candidate
