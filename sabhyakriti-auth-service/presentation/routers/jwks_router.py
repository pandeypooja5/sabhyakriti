from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter(tags=["jwks"])


@router.get("/.well-known/jwks.json")
async def jwks(request: Request) -> dict:
    return request.app.state.jwt_service.get_jwks()
