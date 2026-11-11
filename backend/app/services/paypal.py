from decimal import Decimal
from typing import Any

import httpx

from app.core.config import Settings


class PayPalError(RuntimeError):
    pass


class PayPalGateway:
    def __init__(
        self,
        settings: Settings,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self.settings = settings
        self.transport = transport

    async def _request(
        self,
        method: str,
        path: str,
        *,
        token: str | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        if not self.settings.paypal_client_id or not self.settings.paypal_client_secret:
            raise PayPalError("PayPal sandbox credentials are not configured")
        auth = (self.settings.paypal_client_id, self.settings.paypal_client_secret)
        request_headers = dict(headers or {})
        if token:
            request_headers["Authorization"] = f"Bearer {token}"
        async with httpx.AsyncClient(
            base_url=self.settings.paypal_base_url.rstrip("/"),
            auth=auth if path == "/v1/oauth2/token" else None,
            transport=self.transport,
            timeout=20.0,
        ) as client:
            response = await client.request(
                method,
                path,
                data={"grant_type": "client_credentials"} if path == "/v1/oauth2/token" else None,
                json=json,
                headers=request_headers,
            )
        if response.is_error:
            raise PayPalError(f"PayPal API returned HTTP {response.status_code}")
        payload = response.json()
        if not isinstance(payload, dict):
            raise PayPalError("PayPal returned an unexpected response")
        return payload

    async def _access_token(self) -> str:
        payload = await self._request(
            "POST",
            "/v1/oauth2/token",
            headers={"Accept": "application/json"},
        )
        token = payload.get("access_token")
        if not isinstance(token, str) or not token:
            raise PayPalError("PayPal did not return an access token")
        return token

    async def create_order(
        self,
        *,
        request_id: str,
        offer_id: str,
        amount: Decimal,
        currency: str,
        idempotency_key: str,
    ) -> dict[str, str | None]:
        token = await self._access_token()
        payload = await self._request(
            "POST",
            "/v2/checkout/orders",
            token=token,
            headers={"PayPal-Request-Id": idempotency_key},
            json={
                "intent": "CAPTURE",
                "purchase_units": [
                    {
                        "reference_id": request_id,
                        "custom_id": offer_id,
                        "amount": {
                            "currency_code": currency,
                            "value": f"{amount:.2f}",
                        },
                    }
                ],
                "application_context": {"shipping_preference": "NO_SHIPPING"},
            },
        )
        order_id = payload.get("id")
        if not isinstance(order_id, str) or not order_id:
            raise PayPalError("PayPal order response did not include an order ID")
        approval_url = None
        links = payload.get("links", [])
        if isinstance(links, list):
            for link in links:
                if isinstance(link, dict) and link.get("rel") == "approve":
                    href = link.get("href")
                    approval_url = href if isinstance(href, str) else None
                    break
        return {"order_id": order_id, "approval_url": approval_url}

    async def capture_order(self, order_id: str, idempotency_key: str) -> dict[str, str]:
        token = await self._access_token()
        payload = await self._request(
            "POST",
            f"/v2/checkout/orders/{order_id}/capture",
            token=token,
            headers={"PayPal-Request-Id": idempotency_key},
            json={},
        )
        status = payload.get("status")
        captures = []
        for unit in payload.get("purchase_units", []):
            for capture in unit.get("payments", {}).get("captures", []):
                captures.append(capture)
        capture_id = captures[0].get("id") if captures else None
        if status != "COMPLETED" or not isinstance(capture_id, str):
            raise PayPalError("PayPal did not confirm a completed capture")
        return {"capture_id": capture_id, "status": status}
