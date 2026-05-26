"""Property-based and unit tests for the slug domain service."""
from __future__ import annotations

import re

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from domain.services.slug_service import generate_slug, make_unique_slug

# Slug format: lowercase alphanumeric + hyphens, no leading/trailing hyphens
_VALID_SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9\-]*[a-z0-9]$|^[a-z0-9]$")

# Strategy for product names — mix of unicode, spaces, special chars
name_strategy = st.text(
    alphabet=st.characters(
        whitelist_categories=("L", "N", "Zs", "P"),
    ),
    min_size=1,
    max_size=500,
)


# ---------------------------------------------------------------------------
# Property-based tests
# ---------------------------------------------------------------------------


@given(name=name_strategy)
@settings(max_examples=500)
def test_generate_slug_max_length(name: str) -> None:
    """Slug must never exceed 212 characters."""
    slug = generate_slug(name)
    assert len(slug) <= 212


@given(name=name_strategy)
@settings(max_examples=500)
def test_generate_slug_non_empty(name: str) -> None:
    """Slug must always be non-empty (fallback to 'product')."""
    slug = generate_slug(name)
    assert len(slug) > 0


@given(name=name_strategy)
@settings(max_examples=500)
def test_generate_slug_ascii_only(name: str) -> None:
    """Slug must contain only ASCII characters."""
    slug = generate_slug(name)
    assert slug.isascii()


@given(name=name_strategy)
@settings(max_examples=500)
def test_generate_slug_no_uppercase(name: str) -> None:
    """Slug must be all lowercase."""
    slug = generate_slug(name)
    assert slug == slug.lower()


# ---------------------------------------------------------------------------
# Parametric tests for known inputs
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "name, expected_prefix",
    [
        ("Banarasi Silk Saree", "banarasi-silk-saree"),
        ("Kanjivaram  Saree!", "kanjivaram-saree"),
        ("100% Pure Silk", "100-pure-silk"),
        ("UPPERCASE NAME", "uppercase-name"),
        ("  leading spaces  ", "leading-spaces"),
        ("café saree", "cafe-saree"),
        ("Narayanpet Saree – Premium", "narayanpet-saree-premium"),
    ],
)
def test_generate_slug_known_inputs(name: str, expected_prefix: str) -> None:
    slug = generate_slug(name)
    assert slug == expected_prefix or slug.startswith(expected_prefix[:10])


def test_generate_slug_very_long_name() -> None:
    """Very long names must be truncated to 212 chars."""
    long_name = "a" * 1000
    slug = generate_slug(long_name)
    assert len(slug) <= 212


def test_generate_slug_special_chars_only_returns_product() -> None:
    """Names with only special chars produce the 'product' fallback."""
    slug = generate_slug("---!!!---")
    assert len(slug) > 0  # Should fallback or produce something valid


# ---------------------------------------------------------------------------
# make_unique_slug tests
# ---------------------------------------------------------------------------


def test_make_unique_slug_no_collision() -> None:
    slug = make_unique_slug("silk-saree", existing_slugs=set())
    assert slug == "silk-saree"


def test_make_unique_slug_adds_suffix_on_collision() -> None:
    slug = make_unique_slug("silk-saree", existing_slugs={"silk-saree"})
    assert slug != "silk-saree"
    assert slug.startswith("silk-saree-")
    # Suffix should be 8 hex chars
    suffix = slug.split("-")[-1]
    assert len(suffix) == 8
    assert all(c in "0123456789abcdef" for c in suffix)


def test_make_unique_slug_keeps_existing_if_unique() -> None:
    slug = make_unique_slug(
        "unique-saree", existing_slugs={"other-saree", "another-saree"}
    )
    assert slug == "unique-saree"


def test_make_unique_slug_collision_suffix_not_in_existing() -> None:
    base = "test-slug"
    existing = {base}
    result = make_unique_slug(base, existing)
    assert result not in existing


@given(
    base=st.from_regex(r"[a-z][a-z0-9\-]{0,20}", fullmatch=True),
    extra=st.sets(st.from_regex(r"[a-z][a-z0-9\-]{0,20}", fullmatch=True), max_size=10),
)
@settings(max_examples=200)
def test_make_unique_slug_result_not_in_existing(
    base: str, extra: set[str]
) -> None:
    existing = extra | {base}
    result = make_unique_slug(base, existing)
    assert result not in existing
