from __future__ import annotations

import structlog
from authlib.integrations.httpx_client import AsyncOAuth2Client

log = structlog.get_logger()

_TOKEN_URL = "https://graph.facebook.com/v19.0/oauth/access_token"
_GRAPH_API_URL = "https://graph.facebook.com/v19.0/me"
_FIELDS = "id,name,email,picture"


class FacebookOAuthAdapter:
    """Implements IOAuthAdapter for Facebook Login."""

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
            token = await client.fetch_token(
                url=_TOKEN_URL,
                code=code,
                redirect_uri=redirect_uri,
            )
            log.info("facebook_token_exchanged")
            return dict(token)

    async def get_user_profile(self, access_token: str) -> dict:
        async with AsyncOAuth2Client(token={"access_token": access_token}) as client:
            response = await client.get(
                _GRAPH_API_URL,
                params={"fields": _FIELDS, "access_token": access_token},
            )
            response.raise_for_status()
            data: dict = response.json()
            # Flatten picture url for consistent access
            if "picture" in data and isinstance(data["picture"], dict):
                data["picture"] = data["picture"].get("data", {}).get("url")
            log.info("facebook_profile_fetched", fb_id=data.get("id"))
            return data
