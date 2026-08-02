from __future__ import annotations

from typing import Any

from bitcoin_bastion_sdk.resources.base import BaseResource


class PayRegisterLNURLResource(BaseResource):
    def create_endpoint(self, payload: dict[str, Any]) -> Any:
        return self._post("/payregister/lnurl/endpoints", json=payload, require_auth=True)

    def list_endpoints(self) -> Any:
        return self._get("/payregister/lnurl/endpoints", require_auth=True)

    def create_checkout(self, endpoint_id: str, payload: dict[str, Any]) -> Any:
        return self._post(
            f"/payregister/lnurl/endpoints/{endpoint_id}/checkout",
            json=payload,
            require_auth=True,
        )

    def verify_payment(self, reference: str) -> Any:
        return self._get(f"/payregister/lnurl/pay/verify/{reference}")

    def get_receipt(self, reference: str) -> Any:
        return self._get(f"/payregister/receipts/{reference}", require_auth=True)
