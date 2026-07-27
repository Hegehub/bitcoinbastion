"""Safe public schemas for issuer crypto capability and verification metadata."""

from pydantic import BaseModel, Field


class CryptoCapabilityResponse(BaseModel):
    algorithm: str
    capability_status: str
    provider_name: str | None = None
    provider_version: str | None = None
    can_sign: bool
    can_verify: bool
    hardware_backed: bool
    deterministic_test_vectors_passed: bool
    enabled_in_current_epoch: bool
    operational_notes: str = ""


class IssuerEnvelopeSummaryResponse(BaseModel):
    crypto_epoch: int = Field(ge=1)
    signature_requirement_policy: str
    issuer_key_id: str
    granted_assurance: str
    verified: bool
    requires_reissue: bool
    warnings: list[str] = Field(default_factory=list)


class CryptoCapabilitiesResponse(BaseModel):
    active_crypto_epoch: int
    capabilities: list[CryptoCapabilityResponse]
    pq_implementation_operational: bool = False
