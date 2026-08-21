from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib

OBSERVATION_VERSION = "bitcoin-observation-v1"


class BitcoinObservationType(str, Enum):
    ADDRESS_OBSERVED = "address_observed"
    TRANSACTION_OBSERVED = "transaction_observed"
    FEE_OBSERVED = "fee_observed"
    CONFIRMATION_OBSERVED = "confirmation_observed"


@dataclass(frozen=True, slots=True)
class BitcoinObservationSourceMetadata:
    source_name: str
    source_type: str
    collection_method: str
    network: str = "bitcoin-mainnet"
    rpc_origin: str | None = None
    indexer_origin: str | None = None


@dataclass(frozen=True, slots=True)
class BitcoinObservationProvenance:
    producer: str
    source: BitcoinObservationSourceMetadata
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BitcoinObservation:
    id: str
    observation_version: str
    observation_type: BitcoinObservationType
    producer: str
    observed_at: datetime
    block_height: int | None
    txid: str | None
    confidence: float | None
    provenance: BitcoinObservationProvenance


@dataclass(frozen=True, slots=True)
class AddressObserved(BitcoinObservation):
    address: str = ""
    value_sats: int = 0


@dataclass(frozen=True, slots=True)
class TransactionObserved(BitcoinObservation):
    value_sats: int = 0


@dataclass(frozen=True, slots=True)
class FeeObserved(BitcoinObservation):
    fee_sats: int = 0


@dataclass(frozen=True, slots=True)
class ConfirmationObserved(BitcoinObservation):
    confirmations: int = 0


def stable_observation_id(observation_type: BitcoinObservationType, *parts: str) -> str:
    raw = "\x1f".join((OBSERVATION_VERSION, observation_type.value, *parts))
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"bitcoin_observation:{observation_type.value}:{digest}"
