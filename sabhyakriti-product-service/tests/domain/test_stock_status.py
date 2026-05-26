"""Parametric tests for stock status calculation."""
from __future__ import annotations

import pytest

from domain.services.pricing_service import calculate_stock_status
from domain.value_objects import StockStatus


@pytest.mark.parametrize(
    "qty, expected",
    [
        # Out of stock
        (0, StockStatus.OUT_OF_STOCK),
        (-1, StockStatus.OUT_OF_STOCK),
        (-100, StockStatus.OUT_OF_STOCK),
        # Low stock (default threshold = 5)
        (1, StockStatus.LOW_STOCK),
        (2, StockStatus.LOW_STOCK),
        (3, StockStatus.LOW_STOCK),
        (4, StockStatus.LOW_STOCK),
        (5, StockStatus.LOW_STOCK),
        # In stock
        (6, StockStatus.IN_STOCK),
        (7, StockStatus.IN_STOCK),
        (100, StockStatus.IN_STOCK),
        (10000, StockStatus.IN_STOCK),
    ],
)
def test_calculate_stock_status(qty: int, expected: StockStatus) -> None:
    result = calculate_stock_status(qty)
    assert result == expected, f"qty={qty}: expected {expected}, got {result}"


@pytest.mark.parametrize(
    "qty, threshold, expected",
    [
        (0, 10, StockStatus.OUT_OF_STOCK),
        (1, 10, StockStatus.LOW_STOCK),
        (10, 10, StockStatus.LOW_STOCK),
        (11, 10, StockStatus.IN_STOCK),
        (5, 5, StockStatus.LOW_STOCK),
        (6, 5, StockStatus.IN_STOCK),
    ],
)
def test_calculate_stock_status_custom_threshold(
    qty: int, threshold: int, expected: StockStatus
) -> None:
    result = calculate_stock_status(qty, threshold=threshold)
    assert result == expected


def test_stock_status_out_of_stock_boundary() -> None:
    assert calculate_stock_status(0) == StockStatus.OUT_OF_STOCK


def test_stock_status_low_stock_boundary_lower() -> None:
    assert calculate_stock_status(1) == StockStatus.LOW_STOCK


def test_stock_status_low_stock_boundary_upper() -> None:
    assert calculate_stock_status(5) == StockStatus.LOW_STOCK


def test_stock_status_in_stock_boundary() -> None:
    assert calculate_stock_status(6) == StockStatus.IN_STOCK
