"""Explicit crypto epochs and signature requirement policies."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum

from app.services.access.crypto.algorithms import SignatureAlgorithm


class SignatureRequirementPolicy(StrEnum):
    CLASSICAL_REQUIRED = "classical_required"
    CLASSICAL_REQUIRED_PQ_OPTIONAL = "classical_required_pq_optional"
    HYBRID_REQUIRED = "hybrid_required"
    PQ_REQUIRED = "pq_required"
    LONG_TERM_ROOT_REQUIRED = "long_term_root_required"
    VERIFY_LEGACY_THEN_REISSUE = "verify_legacy_then_reissue"
    UNSUPPORTED = "unsupported"


@dataclass(frozen=True, slots=True)
class CryptoEpochPolicy:
    epoch: int
    effective_from: datetime | None
    allowed_classical_algorithms: frozenset[SignatureAlgorithm]
    allowed_pq_algorithms: frozenset[SignatureAlgorithm]
    default_signature_policy: SignatureRequirementPolicy
    object_type_overrides: dict[str, SignatureRequirementPolicy] = field(default_factory=dict)
    legacy_verification_policy: SignatureRequirementPolicy = (
        SignatureRequirementPolicy.VERIFY_LEGACY_THEN_REISSUE
    )
    reissue_required_before: datetime | None = None
    minimum_client_capabilities: frozenset[str] = frozenset({"ed25519"})
    status: str = "active"

    def requirement_for(self, object_type: str) -> SignatureRequirementPolicy:
        return self.object_type_overrides.get(object_type, self.default_signature_policy)


EPOCH_1 = CryptoEpochPolicy(
    epoch=1,
    effective_from=None,
    allowed_classical_algorithms=frozenset({SignatureAlgorithm.ED25519}),
    allowed_pq_algorithms=frozenset(),
    default_signature_policy=SignatureRequirementPolicy.CLASSICAL_REQUIRED_PQ_OPTIONAL,
    object_type_overrides={"access_certificate": SignatureRequirementPolicy.CLASSICAL_REQUIRED},
)

EPOCH_2_PLANNED = CryptoEpochPolicy(
    epoch=2,
    effective_from=None,
    allowed_classical_algorithms=frozenset({SignatureAlgorithm.ED25519}),
    allowed_pq_algorithms=frozenset({SignatureAlgorithm.ML_DSA_65}),
    default_signature_policy=SignatureRequirementPolicy.HYBRID_REQUIRED,
    status="planned_inactive",
)


class CryptoEpochRegistry:
    def __init__(self, active_epoch: int = 1) -> None:
        self._epochs = {1: EPOCH_1, 2: EPOCH_2_PLANNED}
        if active_epoch != 1:
            raise ValueError("Only crypto epoch 1 is operational")
        self.active_epoch = active_epoch

    def active(self) -> CryptoEpochPolicy:
        return self._epochs[self.active_epoch]

    def get(self, epoch: int) -> CryptoEpochPolicy | None:
        return self._epochs.get(epoch)
