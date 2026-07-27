"""Truthful runtime crypto capability registry."""

from dataclasses import dataclass
from importlib.metadata import version

from app.services.access.crypto.algorithms import (
    CryptoCapabilityStatus,
    PQ_SIGNATURE_ALGORITHMS,
    SignatureAlgorithm,
)


@dataclass(frozen=True, slots=True)
class CryptoCapability:
    algorithm: SignatureAlgorithm
    capability_status: CryptoCapabilityStatus
    provider_name: str | None
    provider_version: str | None
    can_sign: bool
    can_verify: bool
    hardware_backed: bool
    deterministic_test_vectors_passed: bool
    enabled_in_current_epoch: bool
    deprecation_status: str | None = None
    operational_notes: str = ""


class CryptoCapabilityRegistry:
    def __init__(self) -> None:
        self._capabilities = {
            SignatureAlgorithm.ED25519: CryptoCapability(
                SignatureAlgorithm.ED25519,
                CryptoCapabilityStatus.SIGN_AND_VERIFY,
                "cryptography",
                version("cryptography"),
                True,
                True,
                False,
                True,
                True,
                operational_notes="Production classical issuer signature.",
            )
        }
        for algorithm in PQ_SIGNATURE_ALGORITHMS:
            self._capabilities[algorithm] = CryptoCapability(
                algorithm,
                CryptoCapabilityStatus.METADATA_ONLY,
                None,
                None,
                False,
                False,
                False,
                False,
                False,
                operational_notes="No operational provider; metadata only.",
            )

    def get(self, algorithm: SignatureAlgorithm | str) -> CryptoCapability:
        try:
            normalized = SignatureAlgorithm(algorithm)
        except ValueError:
            return CryptoCapability(
                SignatureAlgorithm.UNKNOWN,
                CryptoCapabilityStatus.UNSUPPORTED,
                None,
                None,
                False,
                False,
                False,
                False,
                False,
                operational_notes="Unknown algorithm.",
            )
        return self._capabilities.get(
            normalized,
            CryptoCapability(
                normalized,
                CryptoCapabilityStatus.UNSUPPORTED,
                None,
                None,
                False,
                False,
                False,
                False,
                False,
            ),
        )

    def require_signing(self, algorithm: SignatureAlgorithm | str) -> CryptoCapability:
        capability = self.get(algorithm)
        if not capability.can_sign:
            raise CryptoProviderUnavailable(f"No signing provider for {capability.algorithm.value}")
        return capability

    def require_verification(self, algorithm: SignatureAlgorithm | str) -> CryptoCapability:
        capability = self.get(algorithm)
        if not capability.can_verify:
            raise CryptoProviderUnavailable(
                f"No verification provider for {capability.algorithm.value}"
            )
        return capability

    def report(self) -> tuple[CryptoCapability, ...]:
        return tuple(sorted(self._capabilities.values(), key=lambda item: item.algorithm.value))


class CryptoProviderUnavailable(RuntimeError):
    pass


def validate_crypto_configuration(
    *,
    pq_enabled: bool,
    pq_algorithm: SignatureAlgorithm | str,
    requirement_policy: str,
    registry: CryptoCapabilityRegistry | None = None,
) -> None:
    """Reject configuration that represents unavailable PQ as operational."""
    registry = registry or CryptoCapabilityRegistry()
    if pq_enabled:
        registry.require_signing(pq_algorithm)
        registry.require_verification(pq_algorithm)
    if requirement_policy in {"hybrid_required", "pq_required", "long_term_root_required"}:
        registry.require_signing(pq_algorithm)
