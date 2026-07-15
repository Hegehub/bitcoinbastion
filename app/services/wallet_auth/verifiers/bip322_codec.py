"""BIP-322 parsing, tagged hashing, and Bitcoin address codec helpers.

This module is deterministic and offline-only. It does not sign messages,
broadcast transactions, query chain state, or accept wallet secrets.
"""

from __future__ import annotations

import base64
import hashlib
from dataclasses import dataclass
from enum import StrEnum

from app.domain.wallet_auth.networks import WalletNetwork
from app.domain.wallet_auth.proofs import WalletScriptType

BIP322_MESSAGE_TAG = "BIP0322-signed-message"
MAX_BIP322_MESSAGE_BYTES = 8192
MAX_BIP322_SIGNATURE_BYTES = 131072
MAX_BIP322_WITNESS_ITEMS = 128
MAX_BIP322_WITNESS_ITEM_BYTES = 65536
_BECH32_CHARSET = "qpzry9x8gf2tvdw0s3jn54khce6mua7l"
_BECH32_CHARSET_MAP = {char: idx for idx, char in enumerate(_BECH32_CHARSET)}


class BIP322Variant(StrEnum):
    SIMPLE = "simple"
    FULL = "full"
    PROOF_OF_FUNDS = "proof_of_funds"
    LEGACY = "legacy"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ParsedBIP322Signature:
    variant: BIP322Variant
    payload: bytes
    prefixless: bool = False
    limitations: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DecodedBitcoinAddress:
    address: str
    network: WalletNetwork
    script_type: WalletScriptType
    script_pubkey: bytes
    witness_version: int | None = None
    witness_program: bytes | None = None


class BIP322CodecError(ValueError):
    def __init__(self, reason_code: str) -> None:
        super().__init__(reason_code)
        self.reason_code = reason_code


def bip322_message_hash(message: bytes | str) -> bytes:
    data = message.encode("utf-8") if isinstance(message, str) else message
    if len(data) > MAX_BIP322_MESSAGE_BYTES:
        raise BIP322CodecError("message_too_large")
    tag_hash = hashlib.sha256(BIP322_MESSAGE_TAG.encode("utf-8")).digest()
    return hashlib.sha256(tag_hash + tag_hash + data).digest()


def parse_bip322_signature(value: str, *, allow_prefixless_simple: bool = False) -> ParsedBIP322Signature:
    text = value.strip()
    if not text:
        raise BIP322CodecError("empty_signature")
    if ":" in text:
        prefix, encoded = text.split(":", 1)
    else:
        prefix, encoded = "", text
    limitations: tuple[str, ...]
    if prefix == "":
        if not allow_prefixless_simple:
            raise BIP322CodecError("prefix_required")
        variant = BIP322Variant.SIMPLE
        prefixless = True
        limitations = ("prefixless_compatibility_mode",)
    elif prefix == "smp":
        variant = BIP322Variant.SIMPLE
        prefixless = False
        limitations = ()
    elif prefix == "ful":
        variant = BIP322Variant.FULL
        prefixless = False
        limitations = ()
    elif prefix == "pof":
        variant = BIP322Variant.PROOF_OF_FUNDS
        prefixless = False
        limitations = ()
    else:
        raise BIP322CodecError("unknown_variant")
    try:
        payload = base64.b64decode(encoded, validate=True)
    except Exception as exc:
        raise BIP322CodecError("invalid_base64") from exc
    if not payload:
        raise BIP322CodecError("empty_signature")
    if len(payload) > MAX_BIP322_SIGNATURE_BYTES:
        raise BIP322CodecError("signature_too_large")
    return ParsedBIP322Signature(variant=variant, payload=payload, prefixless=prefixless, limitations=limitations)


def encode_witness_stack(items: tuple[bytes, ...]) -> bytes:
    if len(items) > MAX_BIP322_WITNESS_ITEMS:
        raise BIP322CodecError("too_many_witness_items")
    out = bytearray(_compact_size(len(items)))
    for item in items:
        if len(item) > MAX_BIP322_WITNESS_ITEM_BYTES:
            raise BIP322CodecError("witness_item_too_large")
        out.extend(_compact_size(len(item)))
        out.extend(item)
    return bytes(out)


def decode_witness_stack(payload: bytes) -> tuple[bytes, ...]:
    offset = 0
    count, offset = _read_compact_size(payload, offset)
    if count > MAX_BIP322_WITNESS_ITEMS:
        raise BIP322CodecError("too_many_witness_items")
    items: list[bytes] = []
    for _ in range(count):
        length, offset = _read_compact_size(payload, offset)
        if length > MAX_BIP322_WITNESS_ITEM_BYTES:
            raise BIP322CodecError("witness_item_too_large")
        end = offset + length
        if end > len(payload):
            raise BIP322CodecError("truncated_witness")
        items.append(payload[offset:end])
        offset = end
    if offset != len(payload):
        raise BIP322CodecError("wrong_variant_payload")
    return tuple(items)


def decode_bitcoin_address(address: str, expected_network: WalletNetwork) -> DecodedBitcoinAddress:
    normalized = address.strip()
    if not normalized or normalized != address.strip():
        raise BIP322CodecError("invalid_address")
    hrp, data, spec = _bech32_decode(normalized)
    network = _network_for_hrp(hrp)
    if network == WalletNetwork.BITCOIN_TESTNET and expected_network == WalletNetwork.BITCOIN_SIGNET:
        network = WalletNetwork.BITCOIN_SIGNET
    if network != expected_network:
        raise BIP322CodecError("wrong_network")
    if not data:
        raise BIP322CodecError("invalid_address")
    witness_version = data[0]
    if witness_version > 16:
        raise BIP322CodecError("unsupported_script")
    program = bytes(_convertbits(data[1:], 5, 8, False))
    if len(program) < 2 or len(program) > 40:
        raise BIP322CodecError("invalid_address")
    if witness_version == 0:
        if spec != "bech32":
            raise BIP322CodecError("invalid_address")
        if len(program) == 20:
            script_type = WalletScriptType.P2WPKH
        elif len(program) == 32:
            script_type = WalletScriptType.P2WSH
        else:
            raise BIP322CodecError("unsupported_script")
    elif witness_version == 1 and len(program) == 32:
        if spec != "bech32m":
            raise BIP322CodecError("invalid_address")
        script_type = WalletScriptType.P2TR
    else:
        raise BIP322CodecError("unsupported_script")
    if witness_version == 0:
        script_pubkey = b"\x00" + bytes([len(program)]) + program
    else:
        script_pubkey = bytes([0x50 + witness_version]) + bytes([len(program)]) + program
    return DecodedBitcoinAddress(
        address=normalized,
        network=network,
        script_type=script_type,
        script_pubkey=script_pubkey,
        witness_version=witness_version,
        witness_program=program,
    )


def _network_for_hrp(hrp: str) -> WalletNetwork:
    if hrp == "bc":
        return WalletNetwork.BITCOIN_MAINNET
    if hrp == "tb":
        return WalletNetwork.BITCOIN_TESTNET
    if hrp == "bcrt":
        return WalletNetwork.BITCOIN_REGTEST
    raise BIP322CodecError("wrong_network")


def _bech32_decode(bech: str) -> tuple[str, list[int], str]:
    if bech.lower() != bech and bech.upper() != bech:
        raise BIP322CodecError("invalid_address")
    bech = bech.lower()
    pos = bech.rfind("1")
    if pos < 1 or pos + 7 > len(bech) or len(bech) > 90:
        raise BIP322CodecError("invalid_address")
    hrp = bech[:pos]
    data_chars = bech[pos + 1 :]
    if any(char not in _BECH32_CHARSET_MAP for char in data_chars):
        raise BIP322CodecError("invalid_address")
    data = [_BECH32_CHARSET_MAP[char] for char in data_chars]
    polymod = _bech32_polymod(_bech32_hrp_expand(hrp) + data)
    if polymod == 1:
        spec = "bech32"
    elif polymod == 0x2BC830A3:
        spec = "bech32m"
    else:
        raise BIP322CodecError("invalid_address")
    return hrp, data[:-6], spec


def _bech32_hrp_expand(hrp: str) -> list[int]:
    return [ord(x) >> 5 for x in hrp] + [0] + [ord(x) & 31 for x in hrp]


def _bech32_polymod(values: list[int]) -> int:
    chk = 1
    generator = (0x3B6A57B2, 0x26508E6D, 0x1EA119FA, 0x3D4233DD, 0x2A1462B3)
    for value in values:
        top = chk >> 25
        chk = (chk & 0x1FFFFFF) << 5 ^ value
        for i in range(5):
            if (top >> i) & 1:
                chk ^= generator[i]
    return chk


def _convertbits(data: list[int], frombits: int, tobits: int, pad: bool) -> list[int]:
    acc = 0
    bits = 0
    ret: list[int] = []
    maxv = (1 << tobits) - 1
    max_acc = (1 << (frombits + tobits - 1)) - 1
    for value in data:
        if value < 0 or value >> frombits:
            raise BIP322CodecError("invalid_address")
        acc = ((acc << frombits) | value) & max_acc
        bits += frombits
        while bits >= tobits:
            bits -= tobits
            ret.append((acc >> bits) & maxv)
    if pad:
        if bits:
            ret.append((acc << (tobits - bits)) & maxv)
    elif bits >= frombits or ((acc << (tobits - bits)) & maxv):
        raise BIP322CodecError("invalid_address")
    return ret


def _compact_size(value: int) -> bytes:
    if value < 0xFD:
        return bytes([value])
    if value <= 0xFFFF:
        return b"\xfd" + value.to_bytes(2, "little")
    if value <= 0xFFFFFFFF:
        return b"\xfe" + value.to_bytes(4, "little")
    return b"\xff" + value.to_bytes(8, "little")


def _read_compact_size(payload: bytes, offset: int) -> tuple[int, int]:
    if offset >= len(payload):
        raise BIP322CodecError("truncated_witness")
    first = payload[offset]
    offset += 1
    if first < 0xFD:
        return first, offset
    if first == 0xFD:
        size = 2
    elif first == 0xFE:
        size = 4
    else:
        size = 8
    if offset + size > len(payload):
        raise BIP322CodecError("truncated_witness")
    return int.from_bytes(payload[offset : offset + size], "little"), offset + size
