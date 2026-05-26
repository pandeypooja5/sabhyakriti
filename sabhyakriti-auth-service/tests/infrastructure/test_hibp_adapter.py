from __future__ import annotations

from unittest.mock import AsyncMock, patch

import httpx
import pytest

from infrastructure.adapters.hibp_adapter import HIBPAdapter


@pytest.mark.asyncio
async def test_breached_password_detected() -> None:
    adapter = HIBPAdapter()
    # SHA-1("password") = 5BAA61E4C9B93F3F0682250B6CF8331B7EE68FD8
    # prefix = 5BAA6, suffix = 1E4C9B93F3F0682250B6CF8331B7EE68FD8
    mock_response = AsyncMock()
    mock_response.text = "1E4C9B93F3F0682250B6CF8331B7EE68FD8:12345678\nOTHERHASH:1"
    mock_response.raise_for_status = lambda: None
    with patch("httpx.AsyncClient.get", return_value=mock_response):
        assert await adapter.is_password_breached("password")


@pytest.mark.asyncio
async def test_safe_password_not_detected() -> None:
    adapter = HIBPAdapter()
    mock_response = AsyncMock()
    mock_response.text = "AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA:1"
    mock_response.raise_for_status = lambda: None
    with patch("httpx.AsyncClient.get", return_value=mock_response):
        assert not await adapter.is_password_breached("UniqueAndSafeP@ss9!")


@pytest.mark.asyncio
async def test_timeout_fails_open() -> None:
    adapter = HIBPAdapter()
    with patch("httpx.AsyncClient.get", side_effect=httpx.TimeoutException("timeout")):
        # should return False (fail open) without raising
        result = await adapter.is_password_breached("anypassword")
    assert result is False
