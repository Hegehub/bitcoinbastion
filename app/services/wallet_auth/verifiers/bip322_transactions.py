"""Deterministic BIP-322 virtual transaction construction."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

MAX_BIP322_TRANSACTION_BYTES = 131072


@dataclass(frozen=True, slots=True)
class BIP322VirtualTransactions:
    to_spend: bytes
    to_sign: bytes
    to_spend_txid: str
    to_sign_txid: str


def build_bip322_virtual_transactions(*, message_hash: bytes, message_challenge: bytes) -> BIP322VirtualTransactions:
    script_sig = b"\x00\x20" + message_hash
    to_spend = _serialize_tx(
        version=0,
        inputs=((b"\x00" * 32, 0xFFFFFFFF, script_sig, 0),),
        outputs=((0, message_challenge),),
        locktime=0,
    )
    to_spend_hash = _hash256(to_spend)
    to_sign = _serialize_tx(
        version=0,
        inputs=((to_spend_hash, 0, b"", 0),),
        outputs=((0, b"\x6a"),),
        locktime=0,
    )
    if len(to_spend) > MAX_BIP322_TRANSACTION_BYTES or len(to_sign) > MAX_BIP322_TRANSACTION_BYTES:
        raise ValueError("bip322_transaction_too_large")
    return BIP322VirtualTransactions(
        to_spend=to_spend,
        to_sign=to_sign,
        to_spend_txid=to_spend_hash[::-1].hex(),
        to_sign_txid=_hash256(to_sign)[::-1].hex(),
    )


def _serialize_tx(
    *,
    version: int,
    inputs: tuple[tuple[bytes, int, bytes, int], ...],
    outputs: tuple[tuple[int, bytes], ...],
    locktime: int,
) -> bytes:
    out = bytearray(version.to_bytes(4, "little", signed=True))
    out.extend(_compact_size(len(inputs)))
    for prev_hash, prev_index, script_sig, sequence in inputs:
        out.extend(prev_hash)
        out.extend(prev_index.to_bytes(4, "little"))
        out.extend(_compact_size(len(script_sig)))
        out.extend(script_sig)
        out.extend(sequence.to_bytes(4, "little"))
    out.extend(_compact_size(len(outputs)))
    for value, script_pubkey in outputs:
        out.extend(value.to_bytes(8, "little"))
        out.extend(_compact_size(len(script_pubkey)))
        out.extend(script_pubkey)
    out.extend(locktime.to_bytes(4, "little"))
    return bytes(out)


def _compact_size(value: int) -> bytes:
    if value < 0xFD:
        return bytes([value])
    if value <= 0xFFFF:
        return b"\xfd" + value.to_bytes(2, "little")
    if value <= 0xFFFFFFFF:
        return b"\xfe" + value.to_bytes(4, "little")
    return b"\xff" + value.to_bytes(8, "little")


def _hash256(payload: bytes) -> bytes:
    return hashlib.sha256(hashlib.sha256(payload).digest()).digest()
