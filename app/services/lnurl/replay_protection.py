"""LNURL k1 replay-protection facade."""
from app.services.lnurl.k1_registry import ConsumedK1Context, LNURLK1RegistryService

class LNURLK1ReplayProtection:
    def __init__(self, registry: LNURLK1RegistryService) -> None:
        self.registry = registry

    def consume_once(self, raw_k1: str, **expected: str | None) -> ConsumedK1Context:
        return self.registry.consume_k1(raw_k1, **expected)

__all__ = ["LNURLK1ReplayProtection"]
