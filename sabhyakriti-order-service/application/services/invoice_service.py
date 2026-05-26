"""
Invoice Service — generates PDF invoices using weasyprint + Jinja2.

Produces a compliant Indian GST tax invoice with CGST + SGST breakdown.
"""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path

import structlog
from jinja2 import Environment, FileSystemLoader, select_autoescape

from application.dtos.order_dtos import OrderDTO

logger = structlog.get_logger(__name__)

TEMPLATE_DIR = Path(__file__).parent.parent.parent / "templates"


class InvoiceService:
    """Generates PDF invoice bytes for a given order."""

    def __init__(
        self,
        seller_gstin: str,
        seller_address: str,
    ) -> None:
        self._seller_gstin = seller_gstin
        self._seller_address = seller_address
        self._jinja_env = Environment(
            loader=FileSystemLoader(str(TEMPLATE_DIR)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    async def generate_invoice_pdf(self, order: OrderDTO) -> bytes:
        """
        Render the invoice HTML template and convert to PDF bytes.

        Returns raw PDF bytes suitable for streaming to the client.
        """
        try:
            from weasyprint import HTML  # type: ignore[import-untyped]
        except ImportError as exc:
            raise RuntimeError(
                "weasyprint is not installed. "
                "Run: pip install weasyprint"
            ) from exc

        template = self._jinja_env.get_template("invoice.html")

        context = {
            "order": order,
            "seller_gstin": self._seller_gstin,
            "seller_address": self._seller_address,
            "generated_at": datetime.utcnow().strftime("%d %B %Y %H:%M UTC"),
            "items": order.items,
        }

        html_content = template.render(**context)

        logger.info("generating_invoice", order_number=order.order_number)

        # weasyprint is synchronous; run in executor in production
        pdf_bytes: bytes = HTML(string=html_content).write_pdf()

        logger.info(
            "invoice_generated",
            order_number=order.order_number,
            size_bytes=len(pdf_bytes),
        )
        return pdf_bytes
