from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from application.services.admin_application_service import AdminApplicationService

NOW = datetime.now(tz=timezone.utc)


def _make_order_raw(status: str = "DELIVERED") -> dict:
    return {
        "order_id": str(uuid4()),
        "order_number": "SKB-202605-000001",
        "user_id": str(uuid4()),
        "status": status,
        "total_amount": "1500.00",
        "placed_at": NOW.isoformat(),
        "item_count": 2,
    }


def _make_user_raw() -> dict:
    return {
        "user_id": str(uuid4()),
        "email": "customer@example.com",
        "phone_number": "9876543210",
        "full_name": "Test Customer",
        "is_email_verified": True,
        "created_at": NOW.isoformat(),
        "total_orders": 3,
    }


@pytest.fixture
def mock_order_client():
    m = AsyncMock()
    m.get_dashboard_stats.return_value = {"revenue": "45000.00", "order_count": 30}
    m.get_pending_counts.return_value = {"pending_orders": 5, "pending_returns": 2}
    m.get_recent_orders.return_value = [_make_order_raw() for _ in range(5)]
    m.get_sales_report.return_value = {
        "total_revenue": "45000.00",
        "total_orders": 30,
        "revenue_by_day": [
            {"date": "2026-05-01", "revenue": "3000.00", "order_count": 3}
        ],
    }
    m.get_top_products.return_value = [
        {
            "product_id": str(uuid4()),
            "product_name": "Kanjivaram Silk",
            "units_sold": 10,
            "revenue": "15000.00",
        }
    ]
    m.get_category_revenue.return_value = [
        {"category_name": "Silk", "category_type": "FABRIC", "revenue": "25000.00"}
    ]
    m.get_order_status_breakdown.return_value = {"DELIVERED": 25, "CONFIRMED": 5}
    m.get_orders_by_user.return_value = [_make_order_raw() for _ in range(3)]
    return m


@pytest.fixture
def mock_product_client():
    m = AsyncMock()
    m.get_low_stock_count.return_value = 4
    return m


@pytest.fixture
def mock_auth_client():
    m = AsyncMock()
    m.get_new_customers_count.return_value = 12
    m.list_customers.return_value = {
        "items": [_make_user_raw() for _ in range(3)],
        "total_count": 3,
    }
    m.get_customer.return_value = _make_user_raw()
    return m


@pytest.fixture
def admin_service(mock_order_client, mock_product_client, mock_auth_client):
    return AdminApplicationService(mock_order_client, mock_product_client, mock_auth_client)
