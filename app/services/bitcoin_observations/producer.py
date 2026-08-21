from __future__ import annotations

from dataclasses import dataclass
import json

from app.db.models.onchain import OnchainEvent
from app.db.repositories.onchain_repository import OnchainRepository
from app.integrations.bitcoin.provider import ChainEvent
from app.services.bitcoin_observations.domain import (
    OBSERVATION_VERSION,
    AddressObserved,
    BitcoinObservation,
    BitcoinObservationProvenance,
    BitcoinObservationSourceMetadata,
    BitcoinObservationType,
    ConfirmationObserved,
    FeeObserved,
    TransactionObserved,
    stable_observation_id,
)

PRODUCER_NAME = "BitcoinObservationProducer"


@dataclass(frozen=True, slots=True)
class BitcoinObservationBatch:
    observations: tuple[BitcoinObservation, ...]
    persisted_event: OnchainEvent | None = None


class BitcoinObservationProducer:
    """Canonical producer for immutable factual Bitcoin observations."""

    def __init__(self, repository: OnchainRepository | None = None) -> None:
        self.repository = repository

    def persist_chain_event(
        self,
        event: ChainEvent,
        *,
        significance: float,
        confidence: float,
        explainability: dict[str, float | str] | None = None,
        tags: list[str] | None = None,
    ) -> BitcoinObservationBatch:
        if self.repository is None:
            msg = "OnchainRepository is required to persist chain events"
            raise ValueError(msg)
        model = self.repository.add_event(
            event,
            significance=significance,
            confidence=confidence,
            explainability=explainability,
            tags=tags,
        )
        batch = self.from_onchain_event(model)
        return BitcoinObservationBatch(
            observations=batch.observations, persisted_event=model
        )

    def from_onchain_event(self, event: OnchainEvent) -> BitcoinObservationBatch:
        txid = self._normalize_txid(event.txid)
        address = self._normalize_address(event.address)
        source = self._source_metadata(event)
        limitations = self._limitations(event)
        provenance = BitcoinObservationProvenance(
            producer=PRODUCER_NAME,
            source=source,
            limitations=limitations,
        )
        observations: list[BitcoinObservation] = []
        if txid:
            observations.append(
                TransactionObserved(
                    id=stable_observation_id(
                        BitcoinObservationType.TRANSACTION_OBSERVED,
                        txid,
                        str(event.block_height),
                        str(event.value_sats),
                    ),
                    observation_version=OBSERVATION_VERSION,
                    observation_type=BitcoinObservationType.TRANSACTION_OBSERVED,
                    producer=PRODUCER_NAME,
                    observed_at=event.observed_at,
                    block_height=self._block_height(event.block_height),
                    txid=txid,
                    confidence=event.confidence_score,
                    provenance=provenance,
                    value_sats=event.value_sats,
                )
            )
        if address:
            observations.append(
                AddressObserved(
                    id=stable_observation_id(
                        BitcoinObservationType.ADDRESS_OBSERVED,
                        address,
                        txid or "no-txid",
                        str(event.value_sats),
                    ),
                    observation_version=OBSERVATION_VERSION,
                    observation_type=BitcoinObservationType.ADDRESS_OBSERVED,
                    producer=PRODUCER_NAME,
                    observed_at=event.observed_at,
                    block_height=self._block_height(event.block_height),
                    txid=txid,
                    confidence=event.confidence_score,
                    provenance=provenance,
                    address=address,
                    value_sats=event.value_sats,
                )
            )
        if event.fee_sats > 0 and txid:
            observations.append(
                FeeObserved(
                    id=stable_observation_id(
                        BitcoinObservationType.FEE_OBSERVED, txid, str(event.fee_sats)
                    ),
                    observation_version=OBSERVATION_VERSION,
                    observation_type=BitcoinObservationType.FEE_OBSERVED,
                    producer=PRODUCER_NAME,
                    observed_at=event.observed_at,
                    block_height=self._block_height(event.block_height),
                    txid=txid,
                    confidence=event.confidence_score,
                    provenance=provenance,
                    fee_sats=event.fee_sats,
                )
            )
        if event.block_height > 0 and txid:
            observations.append(
                ConfirmationObserved(
                    id=stable_observation_id(
                        BitcoinObservationType.CONFIRMATION_OBSERVED, txid, str(event.block_height)
                    ),
                    observation_version=OBSERVATION_VERSION,
                    observation_type=BitcoinObservationType.CONFIRMATION_OBSERVED,
                    producer=PRODUCER_NAME,
                    observed_at=event.observed_at,
                    block_height=event.block_height,
                    txid=txid,
                    confidence=event.confidence_score,
                    provenance=provenance,
                    confirmations=1,
                )
            )
        return BitcoinObservationBatch(observations=tuple(sorted(observations, key=lambda item: item.id)))

    def _source_metadata(self, event: OnchainEvent) -> BitcoinObservationSourceMetadata:
        payload = self._payload(event)
        source_type = str(payload.get("source_type", "onchain_event"))
        provider = event.provider.strip() or "onchain_repository"
        indexer_origin = provider if provider in {"esplora", "mempool"} else None
        rpc_origin = provider if provider == "bitcoin_core_rpc" else None
        return BitcoinObservationSourceMetadata(
            source_name=provider,
            source_type=source_type,
            collection_method="onchain_repository_event",
            network=str(payload.get("network", "bitcoin-mainnet")),
            rpc_origin=rpc_origin,
            indexer_origin=indexer_origin,
        )

    def _limitations(self, event: OnchainEvent) -> tuple[str, ...]:
        payload = self._payload(event)
        raw = payload.get("limitations")
        values: list[str] = ["observation_only", "no_relationships", "no_interpretation"]
        if isinstance(raw, str) and raw:
            values.append(raw)
        return tuple(sorted(set(values)))

    def _payload(self, event: OnchainEvent) -> dict[str, str | int | float | bool]:
        try:
            loaded = json.loads(event.raw_payload_json or "{}")
        except json.JSONDecodeError:
            return {}
        if not isinstance(loaded, dict):
            return {}
        out: dict[str, str | int | float | bool] = {}
        for key, value in loaded.items():
            if isinstance(key, str) and isinstance(value, (str, int, float, bool)):
                out[key] = value
        return out

    @staticmethod
    def _normalize_txid(txid: str) -> str:
        return txid.strip().lower()

    @staticmethod
    def _normalize_address(address: str) -> str:
        return address.strip()

    @staticmethod
    def _block_height(block_height: int) -> int | None:
        if block_height <= 0:
            return None
        return block_height
