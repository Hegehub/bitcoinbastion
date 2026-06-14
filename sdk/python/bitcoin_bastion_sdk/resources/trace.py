from __future__ import annotations

from typing import Any

from bitcoin_bastion_sdk.resources.base import AsyncBaseResource, BaseResource
from bitcoin_bastion_sdk.safety import assert_safe


class TraceResource(BaseResource):
    def lite(self, address: str, *, raw: bool = False) -> Any:
        assert_safe(address)
        return self._get(f"/trace/lite/{address}", raw=raw)

    def analyze_address(self, address: str, *, raw: bool = False) -> Any:
        assert_safe(address)
        return self._get(f"/trace/address/{address}", raw=raw)

    def get_report(self, report_id: int | str, *, raw: bool = False) -> Any:
        return self._get(f"/trace/report/{report_id}", raw=raw)

    def get_public_summary(self, report_id: int | str, *, raw: bool = False) -> Any:
        return self._get(f"/public/trace/{report_id}/summary", raw=raw)

    def get_evidence(self, report_id: int | str, *, raw: bool = False) -> Any:
        return self._get(f"/trace/report/{report_id}/evidence", raw=raw)

    def get_proof_packet(self, report_id: int | str, *, raw: bool = False) -> Any:
        return self._get(f"/trace/report/{report_id}/proof-packet", raw=raw)

    def get_privacy_shield(self, report_id: int | str, *, raw: bool = False) -> Any:
        return self._get(f"/trace/report/{report_id}/privacy-shield", raw=raw)

    def get_origin_passport(self, report_id: int | str, *, raw: bool = False) -> Any:
        return self._get(f"/trace/report/{report_id}/origin-passport", raw=raw)

    def get_counterparty_lens(self, report_id: int | str, *, raw: bool = False) -> Any:
        return self._get(f"/trace/report/{report_id}/counterparty-lens", raw=raw)

    def get_policy_facts(self, report_id: int | str, *, raw: bool = False) -> Any:
        return self._get(f"/trace/report/{report_id}/policy-facts", raw=raw)

    def source_summary(self, report_id: int | str, *, raw: bool = False) -> Any:
        return self._get(f"/trace/report/{report_id}/source-summary", raw=raw)

    def provider_disagreement(self, report_id: int | str, *, raw: bool = False) -> Any:
        return self._get(f"/trace/report/{report_id}/provider-disagreement", raw=raw)

    def utxo_hygiene(self, report_id: int | str, *, raw: bool = False) -> Any:
        return self._get(f"/trace/report/{report_id}/utxo-hygiene", raw=raw)

    def dust_radar(self, report_id: int | str, *, raw: bool = False) -> Any:
        return self._get(f"/trace/report/{report_id}/dust-radar", raw=raw)

    def batch(self, addresses: list[str], *, raw: bool = False) -> Any:
        assert_safe(addresses)
        return self._post("/trace/business/batch", json={"addresses": addresses}, raw=raw)

    def treasury_destination_check(self, payload: dict[str, Any], *, raw: bool = False) -> Any:
        assert_safe(payload)
        return self._post("/trace/treasury/destination-check", json=payload, raw=raw)


class AsyncTraceResource(AsyncBaseResource):
    async def lite(self, address: str, *, raw: bool = False) -> Any:
        assert_safe(address)
        return await self._get(f"/trace/lite/{address}", raw=raw)

    async def analyze_address(self, address: str, *, raw: bool = False) -> Any:
        assert_safe(address)
        return await self._get(f"/trace/address/{address}", raw=raw)

    async def get_report(self, report_id: int | str, *, raw: bool = False) -> Any:
        return await self._get(f"/trace/report/{report_id}", raw=raw)

    async def get_public_summary(self, report_id: int | str, *, raw: bool = False) -> Any:
        return await self._get(f"/public/trace/{report_id}/summary", raw=raw)
