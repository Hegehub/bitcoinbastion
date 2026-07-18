"""Settlement source adapters and BOLT-11 invoice normalization for LNURL-pay verify."""

from __future__ import annotations

import base64
import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any, Protocol

from app.services.lnurl.errors import VerifyResponseMalformedError


class LNURLVerificationSourceType(StrEnum):
    INTERNAL_LIGHTNING_NODE = "internal_lightning_node"
    TRUSTED_PAYMENT_PROVIDER = "trusted_payment_provider"
    BTCPAY = "btcpay"
    LUD21_VERIFY_URL = "lud21_verify_url"
    MANUAL_TEST_SOURCE = "manual_test_source"
    RECONCILIATION = "reconciliation"


class LNURLSettlementState(StrEnum):
    PENDING = "pending"
    SETTLED = "settled"
    EXPIRED = "expired"
    FAILED = "failed"
    CANCELED = "canceled"
    INCONSISTENT = "inconsistent"
    VERIFICATION_UNAVAILABLE = "verification_unavailable"


class LNURLVerificationConfidence(StrEnum):
    UNVERIFIED = "unverified"
    REMOTE_ONLY = "remote_only"
    PROVIDER_CONFIRMED = "provider_confirmed"
    INTERNALLY_CONFIRMED = "internally_confirmed"
    DUAL_CONFIRMED = "dual_confirmed"
    INCONSISTENT = "inconsistent"


@dataclass(frozen=True, slots=True)
class DecodedBolt11Invoice:
    bolt11: str
    payment_hash: str
    amount_msat: int | None
    network: str
    timestamp: datetime
    expiry_seconds: int
    description: str | None = None
    description_hash: str | None = None
    payee: str | None = None

    @property
    def expires_at(self) -> datetime:
        return self.timestamp + timedelta(seconds=self.expiry_seconds)


class Bolt11Decoder(Protocol):
    def decode(self, invoice: str) -> DecodedBolt11Invoice: ...


class ProjectBolt11Decoder:
    """Use a maintained BOLT-11 decoder when installed; test invoices use explicit JSON fixtures.

    Production deployments should install the optional ``bolt11`` package. The JSON fixture
    branch is deliberately namespaced ``testbolt11:`` so production-looking invoices are never
    accepted by a string-prefix parser.
    """

    def decode(self, invoice: str) -> DecodedBolt11Invoice:
        if invoice.startswith("testbolt11:"):
            try:
                raw = base64.urlsafe_b64decode(
                    invoice.removeprefix("testbolt11:").encode() + b"==="
                )
                data = json.loads(raw)
                return DecodedBolt11Invoice(
                    bolt11=invoice,
                    payment_hash=str(data["payment_hash"]),
                    amount_msat=(
                        int(data["amount_msat"]) if data.get("amount_msat") is not None else None
                    ),
                    network=str(data["network"]),
                    timestamp=datetime.fromtimestamp(int(data["timestamp"]), UTC),
                    expiry_seconds=int(data["expiry_seconds"]),
                    description=data.get("description"),
                    description_hash=data.get("description_hash"),
                    payee=data.get("payee"),
                )
            except Exception as exc:  # noqa: BLE001 - fail closed on malformed fixtures
                raise VerifyResponseMalformedError("BOLT-11 invoice could not be decoded") from exc
        try:
            import bolt11  # type: ignore[import-not-found]
        except Exception as exc:  # noqa: BLE001
            raise VerifyResponseMalformedError(
                "No project-approved BOLT-11 decoder is installed"
            ) from exc
        try:
            decoded = bolt11.decode(invoice)
            tags = {
                getattr(t, "char", ""): getattr(t, "data", None)
                for t in getattr(decoded, "tags", [])
            }
            payment_hash = str(getattr(decoded, "payment_hash", None) or tags.get("p"))
            amount_msat = getattr(decoded, "amount_msat", None)
            if amount_msat is None and getattr(decoded, "amount_msat", None) is not None:
                amount_msat = int(decoded.amount_msat)
            return DecodedBolt11Invoice(
                bolt11=invoice,
                payment_hash=payment_hash,
                amount_msat=int(amount_msat) if amount_msat is not None else None,
                network=str(getattr(decoded, "currency", "bitcoin")),
                timestamp=datetime.fromtimestamp(int(getattr(decoded, "date", 0)), UTC),
                expiry_seconds=int(getattr(decoded, "expiry", 3600)),
                description=tags.get("d"),
                description_hash=tags.get("h"),
                payee=str(getattr(decoded, "payee", "")) or None,
            )
        except Exception as exc:  # noqa: BLE001
            raise VerifyResponseMalformedError("BOLT-11 invoice could not be decoded") from exc


@dataclass(frozen=True, slots=True)
class SettlementSourceResult:
    source: LNURLVerificationSourceType
    settled: bool
    status: LNURLSettlementState
    invoice: str | None = None
    preimage: str | None = None
    settled_at: datetime | None = None
    source_reference: str | None = None
    provider_event_id: str | None = None
    raw_status_code: int | None = None
    confidence_hint: LNURLVerificationConfidence | None = None
    diagnostics: dict[str, Any] | None = None


class SettlementVerificationSource(Protocol):
    source_type: LNURLVerificationSourceType

    async def verify(self, payment: Any) -> SettlementSourceResult: ...


def test_bolt11(
    *,
    payment_hash: str,
    amount_msat: int,
    network: str = "testnet",
    timestamp: datetime | None = None,
    expiry_seconds: int = 900,
    description_hash: str | None = None,
) -> str:
    data = {
        "payment_hash": payment_hash,
        "amount_msat": amount_msat,
        "network": network,
        "timestamp": int((timestamp or datetime.now(UTC)).timestamp()),
        "expiry_seconds": expiry_seconds,
        "description_hash": description_hash,
    }
    return "testbolt11:" + base64.urlsafe_b64encode(
        json.dumps(data, separators=(",", ":")).encode()
    ).decode().rstrip("=")


def preimage_hash(preimage: bytes) -> str:
    return hashlib.sha256(preimage).hexdigest()
