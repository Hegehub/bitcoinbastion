"""Typed, privacy-safe HTTP transport primitives for generated contracts."""

from .foundation import (
    ContractRegistryEntry,
    HealthOutDTO,
    HttpTransport,
    NormalizedOperation,
    PublicStatusEnvelopeDTO,
    PublicStatusResponseDTO,
    SafeTransportError,
    SecurityMetadata,
)

__all__ = [
    "ContractRegistryEntry",
    "HealthOutDTO",
    "HttpTransport",
    "NormalizedOperation",
    "PublicStatusEnvelopeDTO",
    "PublicStatusResponseDTO",
    "SafeTransportError",
    "SecurityMetadata",
]
