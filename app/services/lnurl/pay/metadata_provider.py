"""LNURL-pay metadata provider boundary.

The production metadata builder lives in :mod:`app.services.lnurl.pay_metadata`.
This module keeps the subscription-request service dependency-injection boundary
stable for Prompt 28 callers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.domain.access.plans import PlanCode
from app.services.lnurl.pay.errors import LNURLPayMetadataError
from app.services.lnurl.pay_metadata import LNURLPayMetadataBuilder, metadata_result_from_json


@dataclass(frozen=True, slots=True)
class LNURLPayMetadataResult:
    metadata: str
    metadata_hash: str
    text_plain: str


class LNURLPayMetadataProvider(Protocol):
    def build_subscription_metadata(
        self,
        *,
        plan_code: PlanCode | str,
        product_code: str,
        billing_period: str,
        locale: str | None,
        pricing_version: str,
    ) -> LNURLPayMetadataResult: ...


class MinimalLNURLPayMetadataProvider:
    def __init__(self, builder: LNURLPayMetadataBuilder | None = None) -> None:
        self.builder = builder or LNURLPayMetadataBuilder()

    def build_subscription_metadata(
        self,
        *,
        plan_code: PlanCode | str,
        product_code: str,
        billing_period: str,
        locale: str | None,
        pricing_version: str,
    ) -> LNURLPayMetadataResult:
        try:
            result = self.builder.build_subscription_metadata(
                plan_code=str(plan_code),
                duration_label=billing_period,
                product_name="Bitcoin Bastion" if product_code == "bastion_access" else product_code,
            )
        except Exception as exc:
            raise LNURLPayMetadataError("LNURL-pay metadata could not be built") from exc
        return LNURLPayMetadataResult(metadata=result.canonical_json, metadata_hash=result.metadata_hash, text_plain=result.plain_text)


def validate_lnurl_pay_metadata(metadata: str) -> LNURLPayMetadataResult:
    try:
        result = metadata_result_from_json(metadata)
    except Exception as exc:
        raise LNURLPayMetadataError("LNURL-pay metadata is invalid") from exc
    return LNURLPayMetadataResult(metadata=result.canonical_json, metadata_hash=result.metadata_hash, text_plain=result.plain_text)
