from __future__ import annotations

import asyncio
import os

import boto3
import structlog
from tenacity import retry, stop_after_attempt, wait_exponential

log = structlog.get_logger()

_VERIFICATION_SUBJECT = "Verify your Sabhyakriti account"
_RESET_SUBJECT = "Reset your Sabhyakriti password"
_IS_DEV = os.getenv("ENVIRONMENT", "development").lower() == "development"


def _verification_body(link: str) -> tuple[str, str]:
    text = f"Click the link to verify your email address:\n{link}\n\nThis link expires in 48 hours."
    html = f"""<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:20px">
  <h2>Verify your email address</h2>
  <p>Click the button below to verify your Sabhyakriti account.</p>
  <p><a href="{link}" style="background:#FF6B2B;color:#fff;padding:12px 24px;text-decoration:none;border-radius:4px;display:inline-block">Verify Email</a></p>
  <p>Or copy and paste this URL into your browser:</p>
  <p style="word-break:break-all">{link}</p>
  <p>This link expires in <strong>48 hours</strong>.</p>
</body>
</html>"""
    return text, html


def _reset_body(link: str) -> tuple[str, str]:
    text = f"Click the link to reset your password:\n{link}\n\nThis link expires in 2 hours."
    html = f"""<!DOCTYPE html>
<html>
<body style="font-family:Arial,sans-serif;max-width:600px;margin:auto;padding:20px">
  <h2>Reset your password</h2>
  <p>We received a request to reset your Sabhyakriti password.</p>
  <p><a href="{link}" style="background:#FF6B2B;color:#fff;padding:12px 24px;text-decoration:none;border-radius:4px;display:inline-block">Reset Password</a></p>
  <p>Or copy and paste this URL:</p>
  <p style="word-break:break-all">{link}</p>
  <p>This link expires in <strong>2 hours</strong>.</p>
</body>
</html>"""
    return text, html


class AWSSESAdapter:
    """Implements IEmailAdapter using Amazon SES.

    In ENVIRONMENT=development, emails are printed to the console instead
    of calling SES — no AWS credentials required for local development.
    """

    def __init__(self, from_address: str, region: str = "ap-south-1") -> None:
        self._from_address = from_address
        self._ses = None if _IS_DEV else boto3.client("ses", region_name=region)

    def _send_sync(self, to_email: str, subject: str, text_body: str, html_body: str) -> None:
        if _IS_DEV or self._ses is None:
            # Dev mode: print to console — check auth-service logs for the link
            log.info(
                "DEV_EMAIL (not sent via SES)",
                to=to_email,
                subject=subject,
                body=text_body,
            )
            return
        self._ses.send_email(
            Source=self._from_address,
            Destination={"ToAddresses": [to_email]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": {
                    "Text": {"Data": text_body, "Charset": "UTF-8"},
                    "Html": {"Data": html_body, "Charset": "UTF-8"},
                },
            },
        )

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=2), reraise=False)
    async def send_verification_email(self, to_email: str, link: str) -> None:
        log.info("ses_send_verification", email_domain=to_email.split("@")[-1])
        text, html = _verification_body(link)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: self._send_sync(to_email, _VERIFICATION_SUBJECT, text, html))

    @retry(stop=stop_after_attempt(2), wait=wait_exponential(multiplier=1, min=1, max=2), reraise=False)
    async def send_password_reset_email(self, to_email: str, link: str) -> None:
        log.info("ses_send_password_reset", email_domain=to_email.split("@")[-1])
        text, html = _reset_body(link)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, lambda: self._send_sync(to_email, _RESET_SUBJECT, text, html))
