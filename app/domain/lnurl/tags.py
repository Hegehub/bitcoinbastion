"""LNURL tag and adapter domain enums."""

from __future__ import annotations

from enum import StrEnum


class LNURLTag(StrEnum):
    LOGIN = "login"
    PAY_REQUEST = "payRequest"
    WITHDRAW_REQUEST = "withdrawRequest"


class LNURLAdapterType(StrEnum):
    LNURL_AUTH = "lnurl_auth"
    LNURL_PAY = "lnurl_pay"
    LIGHTNING_ADDRESS = "lightning_address"
    LNURL_WITHDRAW = "lnurl_withdraw"
    LNURL_VERIFY = "lnurl_verify"
    LNURL_PAYERDATA_AUTH = "lnurl_payerdata_auth"
    LNURL_SUCCESS_ACTION = "lnurl_success_action"
