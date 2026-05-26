from __future__ import annotations

from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest

from application.services.admin_application_service import AdminApplicationService


@pytest.mark.asyncio
async def test_dashboard_full_success(admin_service: AdminApplicationService) -> None:
    dto = await admin_service.get_dashboard()
    assert dto.revenue_30d == Decimal("45000.00")
    assert dto.orders_30d == 30
    assert dto.new_customers_30d == 12
    assert dto.low_stock_products == 4
    assert dto.pending_orders == 5
    assert dto.pending_returns == 2
    assert len(dto.recent_orders) == 5
    assert dto.service_unavailable is False


@pytest.mark.asyncio
async def test_dashboard_product_service_down(mock_order_client, mock_auth_client) -> None:
    product_client = AsyncMock()
    product_client.get_low_stock_count.side_effect = ConnectionError("Product Service down")
    svc = AdminApplicationService(mock_order_client, product_client, mock_auth_client)
    dto = await svc.get_dashboard()
    assert dto.low_stock_products == 0
    assert dto.service_unavailable is True
    # Other KPIs still populated
    assert dto.revenue_30d == Decimal("45000.00")


@pytest.mark.asyncio
async def test_dashboard_all_services_down(mock_order_client) -> None:
    failing = AsyncMock()
    failing.get_low_stock_count.side_effect = ConnectionError
    failing.get_new_customers_count.side_effect = ConnectionError
    order_fail = AsyncMock()
    order_fail.get_dashboard_stats.side_effect = ConnectionError
    order_fail.get_pending_counts.side_effect = ConnectionError
    order_fail.get_recent_orders.side_effect = ConnectionError
    svc = AdminApplicationService(order_fail, failing, failing)
    dto = await svc.get_dashboard()
    assert dto.service_unavailable is True
    assert dto.revenue_30d == Decimal("0")
    assert dto.recent_orders == []


@pytest.mark.asyncio
async def test_sales_report_success(admin_service: AdminApplicationService) -> None:
    dto = await admin_service.get_sales_report(date(2026, 5, 1), date(2026, 5, 31))
    assert dto.total_revenue == Decimal("45000.00")
    assert dto.total_orders == 30
    assert len(dto.revenue_by_day) == 1
    assert len(dto.top_products) == 1
    assert len(dto.category_revenue) == 1
    assert dto.service_unavailable is False


@pytest.mark.asyncio
async def test_sales_report_max_range_exceeded(admin_service: AdminApplicationService) -> None:
    with pytest.raises(ValueError, match="365"):
        await admin_service.get_sales_report(date(2025, 1, 1), date(2026, 12, 31))


@pytest.mark.asyncio
async def test_sales_report_invalid_date_order(admin_service: AdminApplicationService) -> None:
    with pytest.raises(ValueError, match="before or equal"):
        await admin_service.get_sales_report(date(2026, 5, 31), date(2026, 5, 1))


@pytest.mark.asyncio
async def test_list_customers(admin_service: AdminApplicationService) -> None:
    dto = await admin_service.list_customers(page=1, page_size=10)
    assert len(dto.items) == 3
    assert dto.total_count == 3
    assert dto.page == 1


@pytest.mark.asyncio
async def test_get_customer_detail_success(admin_service: AdminApplicationService) -> None:
    from uuid import uuid4
    dto = await admin_service.get_customer_detail(uuid4())
    assert dto.user.email == "customer@example.com"
    assert len(dto.orders) == 3
    assert dto.user.total_orders == 3


@pytest.mark.asyncio
async def test_get_customer_detail_orders_fail(
    mock_order_client, mock_product_client, mock_auth_client
) -> None:
    mock_order_client.get_orders_by_user.side_effect = ConnectionError("Order down")
    svc = AdminApplicationService(mock_order_client, mock_product_client, mock_auth_client)
    from uuid import uuid4
    dto = await svc.get_customer_detail(uuid4())
    # User still returned; orders gracefully empty
    assert dto.user is not None
    assert dto.orders == []


@pytest.mark.asyncio
async def test_get_customer_detail_user_not_found(
    mock_order_client, mock_product_client
) -> None:
    auth_fail = AsyncMock()
    auth_fail.get_customer.side_effect = ValueError("User not found")
    auth_fail.get_new_customers_count.return_value = 0
    auth_fail.list_customers.return_value = {"items": [], "total_count": 0}
    svc = AdminApplicationService(mock_order_client, mock_product_client, auth_fail)
    from uuid import uuid4
    with pytest.raises(ValueError, match="not found"):
        await svc.get_customer_detail(uuid4())
