"""LNURL principal domain enums."""

from __future__ import annotations

from enum import StrEnum


class LightningPrincipalType(StrEnum):
    LNURL_AUTH_PRINCIPAL = "lnurl_auth_principal"
    LIGHTNING_ADDRESS_PRINCIPAL = "lightning_address_principal"
    PAYERDATA_AUTH_PRINCIPAL = "payerdata_auth_principal"
