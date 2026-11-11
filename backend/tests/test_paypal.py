from decimal import Decimal

import httpx
import pytest

from app.core.config import Settings
from app.services.paypal import PayPalError, PayPalGateway


@pytest.mark.asyncio
async def test_paypal_gateway_creates_order_and_extracts_approval_link():
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path == "/v1/oauth2/token":
            return httpx.Response(200, json={"access_token": "sandbox-token"})
        assert request.headers["Authorization"] == "Bearer sandbox-token"
        assert request.headers["PayPal-Request-Id"] == "request-key-1"
        body = __import__("json").loads(request.content)
        assert body["purchase_units"][0]["amount"] == {
            "currency_code": "INR",
            "value": "1250.00",
        }
        return httpx.Response(
            201,
            json={
                "id": "ORDER-123",
                "status": "CREATED",
                "links": [{"rel": "approve", "href": "https://sandbox.paypal.test/approve"}],
            },
        )

    gateway = PayPalGateway(
        Settings(paypal_client_id="client", paypal_client_secret="secret"),
        transport=httpx.MockTransport(handler),
    )
    result = await gateway.create_order(
        request_id="request-1",
        offer_id="offer-1",
        amount=Decimal(1250),
        currency="INR",
        idempotency_key="request-key-1",
    )
    assert result == {
        "order_id": "ORDER-123",
        "approval_url": "https://sandbox.paypal.test/approve",
    }


@pytest.mark.asyncio
async def test_paypal_gateway_requires_configured_sandbox_credentials():
    gateway = PayPalGateway(Settings())
    with pytest.raises(PayPalError, match="credentials are not configured"):
        await gateway.create_order(
            request_id="request-1",
            offer_id="offer-1",
            amount=Decimal(1250),
            currency="INR",
            idempotency_key="request-key-1",
        )
