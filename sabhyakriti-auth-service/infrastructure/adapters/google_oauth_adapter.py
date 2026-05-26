from __future__ import annotations

import structlog
from authlib.integrations.httpx_client import AsyncOAuth2Client

log = structlog.get_logger()

_TOKEN_URL = "https://oauth2.googleapis.com/token"
_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


class GoogleOAuthAdapter:
    """Implements IOAuthAdapter for Google Sign-In."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret

    async def exchange_code(
        self,
        code: str,
        redirect_uri: str,
        code_verifier: str | None = None,
    ) -> dict:
        async with AsyncOAuth2Client(
            client_id=self._client_id,
            client_secret=self._client_secret,
            redirect_uri=redirect_uri,
        ) as client:
            kwargs: dict = {
                "url": _TOKEN_URL,
                "code": code,
                "redirect_uri": redirect_uri,
            }
            if code_verifier:
                kwargs["code_verifier"] = code_verifier
            token = await client.fetch_token(**kwargs)
            log.info("google_token_exchanged")
            return dict(token)

    async def get_user_profile(self, access_token: str) -> dict:
        async with AsyncOAuth2Client(token={"access_token": access_token}) as client:
            response = await client.get(_USERINFO_URL)
            response.raise_for_status()
            profile: dict = response.json()
            log.info("google_profile_fetched", sub=profile.get("sub"))
            return profile
