"""Typed, privacy-safe HTTP transport primitives for generated contracts."""

from .foundation import (
    ContractRegistryEntry,
    HealthOutDTO,
    HttpTransport,
    NoContentDTO,
    NormalizedOperation,
    OpaqueHtmlDocumentDTO,
    PublicStatusEnvelopeDTO,
    PublicStatusResponseDTO,
    SafeTransportError,
    SecurityMetadata,
    TextResponseDTO,
)

__all__ = [
    "ContractRegistryEntry",
    "HealthOutDTO",
    "HttpTransport",
    "NoContentDTO",
    "NormalizedOperation",
    "OpaqueHtmlDocumentDTO",
    "PublicStatusEnvelopeDTO",
    "PublicStatusResponseDTO",
    "SafeTransportError",
    "SecurityMetadata",
    "TextResponseDTO",
]
