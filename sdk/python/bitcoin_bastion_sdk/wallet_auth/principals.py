from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class WalletPrincipal:
    principal_id: str
    principal_type: str
    proof_method: str
    verification_strength: str
    status: str
    created_at: datetime | None = None
    last_verified_at: datetime | None = None
    auth_domain: str | None = None


BitcoinWalletPrincipal = WalletPrincipal
LightningWalletPrincipal = WalletPrincipal
