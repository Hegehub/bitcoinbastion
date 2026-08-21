from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib

from app.services.bitcoin_observations.domain import BitcoinObservationSourceMetadata

RELATIONSHIP_VERSION = "bitcoin-topology-relationship-v1"


class BitcoinTopologyObjectType(str, Enum):
    ADDRESS = "address"
    TRANSACTION = "transaction"


class BitcoinTopologyRelationshipType(str, Enum):
    ADDRESS_PARTICIPATES_IN_TRANSACTION = "address_participates_in_transaction"


class BitcoinTopologyDirection(str, Enum):
    DIRECTED = "directed"


@dataclass(frozen=True, slots=True)
class BitcoinTopologyObjectRef:
    object_type: BitcoinTopologyObjectType
    object_id: str
    value: str
    network: str = "bitcoin-mainnet"


@dataclass(frozen=True, slots=True)
class BitcoinTopologyProvenance:
    producer: str
    builder_version: str
    originating_observation_ids: tuple[str, ...]
    source: BitcoinObservationSourceMetadata
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class BitcoinTopologyRelationship:
    id: str
    relationship_version: str
    relationship_type: BitcoinTopologyRelationshipType
    direction: BitcoinTopologyDirection
    source: BitcoinTopologyObjectRef
    target: BitcoinTopologyObjectRef
    producer: str
    created_at: datetime
    provenance: BitcoinTopologyProvenance
    limitations: tuple[str, ...] = ()


def stable_topology_object_id(
    object_type: BitcoinTopologyObjectType,
    value: str,
    *,
    network: str = "bitcoin-mainnet",
) -> str:
    raw = "\x1f".join((RELATIONSHIP_VERSION, network, object_type.value, value))
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"bitcoin_topology_object:{object_type.value}:{digest}"


def stable_relationship_id(
    relationship_type: BitcoinTopologyRelationshipType,
    source: BitcoinTopologyObjectRef,
    target: BitcoinTopologyObjectRef,
    originating_observation_ids: tuple[str, ...],
) -> str:
    raw = "\x1f".join(
        (
            RELATIONSHIP_VERSION,
            relationship_type.value,
            source.object_id,
            target.object_id,
            *originating_observation_ids,
        )
    )
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]
    return f"bitcoin_topology_relationship:{relationship_type.value}:{digest}"
