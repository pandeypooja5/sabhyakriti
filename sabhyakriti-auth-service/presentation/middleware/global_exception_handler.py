from __future__ import annotations

import structlog
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

log = structlog.get_logger()


def _get_request_id(request: Request) -> str:
    return getattr(request.state, "request_id", "unknown")


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        log.warning(
            "request_value_error",
            request_id=_get_request_id(request),
            detail=str(exc),
            path=request.url.path,
        )
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc), "request_id": _get_request_id(request)},
        )

    @app.exception_handler(PermissionError)
    async def permission_error_handler(
        request: Request, exc: PermissionError
    ) -> JSONResponse:
        log.warning(
            "request_permission_error",
            request_id=_get_request_id(request),
            detail=str(exc),
            path=request.url.path,
        )
        return JSONResponse(
            status_code=403,
            content={"detail": str(exc), "request_id": _get_request_id(request)},
        )

    @app.exception_handler(LookupError)
    async def lookup_error_handler(
        request: Request, exc: LookupError
    ) -> JSONResponse:
        log.warning(
            "request_lookup_error",
            request_id=_get_request_id(request),
            detail=str(exc),
            path=request.url.path,
        )
        return JSONResponse(
            status_code=423,
            content={"detail": str(exc), "request_id": _get_request_id(request)},
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        log.exception(
            "unhandled_exception",
            request_id=_get_request_id(request),
            path=request.url.path,
            exc_type=type(exc).__name__,
        )
        return JSONResponse(
            status_code=500,
            content={
                "detail": "An unexpected error occurred",
                "request_id": _get_request_id(request),
            },
        )
