"""Transparent reverse-proxy routes for admin operations on downstream services.

All routes require a valid admin JWT. The Authorization header is forwarded
unchanged to the target service. Downstream errors are surfaced as-is to
preserve HTTP semantics for the admin frontend.
"""

from __future__ import annotations

from typing import Annotated, Any

import httpx
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse

from application.clients.cart_service_client import CartServiceClient
from application.clients.order_service_client import OrderServiceClient
from application.clients.product_service_client import ProductServiceClient
from presentation.dependencies import forward_headers, require_admin

logger = structlog.get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin-proxy"],
)

AdminUser = Annotated[dict[str, Any], Depends(require_admin)]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_product_client(request: Request) -> ProductServiceClient:
    client: ProductServiceClient = request.app.state.product_client
    return client


def _get_order_client(request: Request) -> OrderServiceClient:
    client: OrderServiceClient = request.app.state.order_client
    return client


def _get_cart_client(request: Request) -> CartServiceClient:
    client: CartServiceClient = request.app.state.cart_client
    return client


async def _proxy(
    downstream_response: httpx.Response,
) -> Response:
    """Convert an httpx response into a FastAPI Response, streaming the body."""
    # Exclude hop-by-hop headers that should not be forwarded
    excluded_headers = {
        "transfer-encoding",
        "connection",
        "keep-alive",
        "proxy-authenticate",
        "proxy-authorization",
        "te",
        "trailers",
        "upgrade",
    }
    headers = {
        k: v
        for k, v in downstream_response.headers.items()
        if k.lower() not in excluded_headers
    }
    return Response(
        content=downstream_response.content,
        status_code=downstream_response.status_code,
        headers=headers,
    )


async def _safe_proxy(
    client: ProductServiceClient | OrderServiceClient | CartServiceClient,
    method: str,
    path: str,
    **kwargs: Any,
) -> Response:
    """Proxy the request and surface any httpx / downstream errors as HTTP errors."""
    try:
        downstream = await client.proxy_request(method, path, **kwargs)
        return await _proxy(downstream)
    except httpx.TimeoutException as exc:
        logger.error("proxy.timeout", path=path, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Downstream service timed out",
        ) from exc
    except httpx.HTTPError as exc:
        logger.error("proxy.http_error", path=path, error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Downstream service error",
        ) from exc


# ---------------------------------------------------------------------------
# Product Service proxy  →  /api/v1/admin/products/* and /categories/*
# ---------------------------------------------------------------------------

@router.api_route(
    "/products/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema=True,
    summary="Proxy: Product Service — product management",
)
async def proxy_products(
    path: str,
    request: Request,
    _: AdminUser,
    product_client: Annotated[ProductServiceClient, Depends(_get_product_client)],
) -> Response:
    headers = forward_headers(request)
    downstream_path = f"/api/v1/admin/products/{path}"

    # Handle multipart for bulk-import
    if "multipart/form-data" in request.headers.get("content-type", ""):
        form = await request.form()
        files: dict[str, Any] = {}
        data: dict[str, Any] = {}
        for field_name, field_value in form.multi_items():
            if hasattr(field_value, "read"):
                content = await field_value.read()  # type: ignore[attr-defined]
                files[field_name] = (
                    getattr(field_value, "filename", field_name),
                    content,
                    getattr(field_value, "content_type", "application/octet-stream"),
                )
            else:
                data[field_name] = field_value
        return await _safe_proxy(
            product_client,
            request.method,
            downstream_path,
            headers=headers,
            files=files or None,
            data=data or None,
        )

    body = await request.body()
    return await _safe_proxy(
        product_client,
        request.method,
        downstream_path,
        headers={**headers, "content-type": request.headers.get("content-type", "")},
        content=body or None,
        params=dict(request.query_params),
    )


@router.api_route(
    "/categories/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema=True,
    summary="Proxy: Product Service — category management",
)
async def proxy_categories(
    path: str,
    request: Request,
    _: AdminUser,
    product_client: Annotated[ProductServiceClient, Depends(_get_product_client)],
) -> Response:
    headers = forward_headers(request)
    body = await request.body()
    downstream_path = f"/api/v1/admin/categories/{path}"
    return await _safe_proxy(
        product_client,
        request.method,
        downstream_path,
        headers={**headers, "content-type": request.headers.get("content-type", "")},
        content=body or None,
        params=dict(request.query_params),
    )


# ---------------------------------------------------------------------------
# Order Service proxy  →  /api/v1/admin/orders/* and /returns/*
# ---------------------------------------------------------------------------

@router.api_route(
    "/orders",
    methods=["GET", "POST"],
    include_in_schema=True,
    summary="Proxy: Order Service — list/create orders (admin)",
)
async def proxy_orders_root(
    request: Request,
    _: AdminUser,
    order_client: Annotated[OrderServiceClient, Depends(_get_order_client)],
) -> Response:
    headers = forward_headers(request)
    body = await request.body()
    return await _safe_proxy(
        order_client,
        request.method,
        "/api/v1/admin/orders",
        headers={**headers, "content-type": request.headers.get("content-type", "")},
        content=body or None,
        params=dict(request.query_params),
    )


@router.api_route(
    "/orders/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema=True,
    summary="Proxy: Order Service — order management",
)
async def proxy_orders(
    path: str,
    request: Request,
    _: AdminUser,
    order_client: Annotated[OrderServiceClient, Depends(_get_order_client)],
) -> Response:
    headers = forward_headers(request)
    body = await request.body()
    downstream_path = f"/api/v1/admin/orders/{path}"
    return await _safe_proxy(
        order_client,
        request.method,
        downstream_path,
        headers={**headers, "content-type": request.headers.get("content-type", "")},
        content=body or None,
        params=dict(request.query_params),
    )


@router.api_route(
    "/returns/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema=True,
    summary="Proxy: Order Service — return management",
)
async def proxy_returns(
    path: str,
    request: Request,
    _: AdminUser,
    order_client: Annotated[OrderServiceClient, Depends(_get_order_client)],
) -> Response:
    headers = forward_headers(request)
    body = await request.body()
    downstream_path = f"/api/v1/admin/returns/{path}"
    return await _safe_proxy(
        order_client,
        request.method,
        downstream_path,
        headers={**headers, "content-type": request.headers.get("content-type", "")},
        content=body or None,
        params=dict(request.query_params),
    )


# ---------------------------------------------------------------------------
# Cart Service proxy  →  /api/v1/admin/coupons/*
# ---------------------------------------------------------------------------

@router.api_route(
    "/coupons/{path:path}",
    methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    include_in_schema=True,
    summary="Proxy: Cart Service — coupon management",
)
async def proxy_coupons(
    path: str,
    request: Request,
    _: AdminUser,
    cart_client: Annotated[CartServiceClient, Depends(_get_cart_client)],
) -> Response:
    headers = forward_headers(request)
    body = await request.body()
    downstream_path = f"/api/v1/admin/coupons/{path}"
    return await _safe_proxy(
        cart_client,
        request.method,
        downstream_path,
        headers={**headers, "content-type": request.headers.get("content-type", "")},
        content=body or None,
        params=dict(request.query_params),
    )
