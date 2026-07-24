"""LNURL-withdraw BOLT-11 decoder boundary.

The callback verifier depends on this narrow abstraction so it never accepts
regex-only invoice validation. The default implementation delegates to the
project-approved decoder used by LNURL settlement verification.
"""
from __future__ import annotations

from typing import Protocol

from app.services.lnurl.verification_sources import DecodedBolt11Invoice, ProjectBolt11Decoder


class Bolt11InvoiceDecoder(Protocol):
    def decode(self, invoice: str) -> DecodedBolt11Invoice: ...


__all__ = ["Bolt11InvoiceDecoder", "DecodedBolt11Invoice", "ProjectBolt11Decoder"]
