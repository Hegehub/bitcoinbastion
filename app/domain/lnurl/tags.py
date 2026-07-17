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
    LNURL_WITHDRAW = "lnurl_withdraw"
    LNURL_VERIFY = "lnurl_verify"
    LIGHTNING_ADDRESS = "lightning_address"
    PAYER_DATA = "payer_data"
    SUCCESS_ACTION = "success_action"
    LNURL_PAYERDATA_AUTH = "payer_data"
    LNURL_SUCCESS_ACTION = "success_action"
