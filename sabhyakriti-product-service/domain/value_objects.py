"""Domain value objects for the product service."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class CategoryType(StrEnum):
    """Dimension type for product categories."""

    FABRIC = "FABRIC"
    OCCASION = "OCCASION"
    REGION = "REGION"


class StockStatus(StrEnum):
    """Stock availability status."""

    IN_STOCK = "IN_STOCK"
    LOW_STOCK = "LOW_STOCK"
    OUT_OF_STOCK = "OUT_OF_STOCK"


class SortOrder(StrEnum):
    """Product list sort options."""

    NEWEST = "NEWEST"
    PRICE_ASC = "PRICE_ASC"
    PRICE_DESC = "PRICE_DESC"
    RATING_DESC = "RATING_DESC"
    POPULARITY = "POPULARITY"


@dataclass(frozen=True)
class Money:
    """Immutable money value object."""

    amount: Decimal
    currency: str = "INR"

    def __post_init__(self) -> None:
        if self.amount < Decimal("0"):
            raise ValueError("Money amount cannot be negative")
        if not self.currency:
            raise ValueError("Currency code cannot be empty")

    def __add__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot add {self.currency} and {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: "Money") -> "Money":
        if self.currency != other.currency:
            raise ValueError(f"Cannot subtract {self.currency} and {other.currency}")
        result = self.amount - other.amount
        if result < Decimal("0"):
            raise ValueError("Money subtraction resulted in negative amount")
        return Money(result, self.currency)

    def __str__(self) -> str:
        return f"{self.currency} {self.amount:.2f}"
