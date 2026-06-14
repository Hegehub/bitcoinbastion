from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

SENSITIVE_PATTERNS = (
    "seed phrase",
    "mnemonic",
    "private key",
    "xprv",
    "yprv",
    "zprv",
    "wallet.dat",
    "keystore",
    "12 words",
    "24 words",
    "signing material",
    "recovery phrase",
)

FORBIDDEN_OUTPUT_PHRASES = (
    "clean address",
    "dirty address",
    "criminal address",
    "guaranteed safe",
    "approved payment",
    "verified illicit",
    "guaranteed profit",
    "price will",
    "must buy",
    "must sell",
)

TRACE_SAFETY_TEXT = (
    "Advisory-only. Not legal verification. Not Bitcoin consensus proof. No custody. "
    "Public Bitcoin addresses only. Never enter seed phrases, private keys, wallet files or signing material."
)
MARKET_SAFETY_TEXT = (
    "Historical similarity does not guarantee future market behavior. "
    "Correlation is not proof of causation. Not financial advice."
)
NO_CUSTODY_TEXT = "No custody. Never enter seed phrases, private keys, wallet files or signing material."


class BastionMCPSafetyError(ValueError):
    """Raised when MCP input or output violates Bitcoin Bastion safety rules."""


class BastionMCPToolError(RuntimeError):
    """Raised when an MCP tool cannot safely complete."""


def scan_for_sensitive_material(value: Any) -> list[str]:
    text = _flatten_text(value).casefold()
    return [pattern for pattern in SENSITIVE_PATTERNS if pattern in text]


def assert_no_sensitive_material(value: Any) -> None:
    matches = scan_for_sensitive_material(value)
    if matches:
        raise BastionMCPSafetyError(
            "Never enter seed phrases, private keys, wallet files or signing material."
        )


def scan_for_forbidden_wording(value: Any) -> list[str]:
    text = _flatten_text(value).casefold()
    return [phrase for phrase in FORBIDDEN_OUTPUT_PHRASES if phrase in text]


def assert_no_forbidden_wording(value: Any) -> None:
    matches = scan_for_forbidden_wording(value)
    if matches:
        raise BastionMCPSafetyError("MCP response contained forbidden wording.")


def safety_flags(*, trace: bool = False, market: bool = False, no_custody: bool = True) -> dict[str, bool]:
    return {
        "no_custody": no_custody,
        "advisory_only": trace,
        "not_legal_verification": trace,
        "not_bitcoin_consensus_proof": trace,
        "not_financial_advice": market,
        "draft_only": False,
    }


def enforce_treasury_draft_only(payload: Mapping[str, Any]) -> None:
    text = _flatten_text(payload).casefold()
    forbidden_actions = ("approve", "broadcast", "sign", "execute", "move funds")
    if any(action in text for action in forbidden_actions):
        raise BastionMCPSafetyError("Treasury MCP tools are draft-only and require human approval.")


def _flatten_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        return " ".join(f"{key} {_flatten_text(item)}" for key, item in value.items())
    if isinstance(value, Sequence) and not isinstance(value, (bytes, bytearray)):
        return " ".join(_flatten_text(item) for item in value)
    return str(value)
