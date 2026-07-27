"""Domain-separated deterministic SHA-256 Merkle tree."""

import hashlib
from collections.abc import Sequence

from .models import MerkleProofStep

EMPTY_DOMAIN = b"BASTION_TRANSPARENCY_EMPTY_V1\x00"
NODE_DOMAIN = b"BASTION_TRANSPARENCY_NODE_V1\x00"


def _raw(value: str) -> bytes:
    text = value.removeprefix("sha256:")
    if len(text) != 64:
        raise ValueError("Merkle hash must be a SHA-256 digest")
    return bytes.fromhex(text)


def _node(left: str, right: str) -> str:
    return "sha256:" + hashlib.sha256(NODE_DOMAIN + _raw(left) + _raw(right)).hexdigest()


def deterministic_empty_root() -> str:
    return "sha256:" + hashlib.sha256(EMPTY_DOMAIN).hexdigest()


def deterministic_leaf_ordering(leaf_hashes: Sequence[str]) -> tuple[str, ...]:
    """Sort hashes; duplicate commitments remain explicit leaves and affect source_count/root."""
    return tuple(sorted(leaf_hashes))


def build_merkle_root(leaf_hashes: Sequence[str]) -> str:
    level = list(deterministic_leaf_ordering(leaf_hashes))
    if not level:
        return deterministic_empty_root()
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])  # Bitcoin-style duplicate-last, committed by this version.
        level = [_node(level[index], level[index + 1]) for index in range(0, len(level), 2)]
    return level[0]


def build_merkle_proof(leaf_hashes: Sequence[str], target_index: int) -> tuple[MerkleProofStep, ...]:
    ordered = list(deterministic_leaf_ordering(leaf_hashes))
    if target_index < 0 or target_index >= len(ordered):
        raise IndexError("Merkle target index out of range")
    index = target_index
    proof: list[MerkleProofStep] = []
    while len(ordered) > 1:
        if len(ordered) % 2:
            ordered.append(ordered[-1])
        sibling = index - 1 if index % 2 else index + 1
        proof.append(MerkleProofStep(ordered[sibling], sibling < index))
        ordered = [_node(ordered[pos], ordered[pos + 1]) for pos in range(0, len(ordered), 2)]
        index //= 2
    return tuple(proof)


def verify_merkle_proof(
    leaf_hash: str, proof: Sequence[MerkleProofStep], root_hash: str
) -> bool:
    current = leaf_hash
    try:
        for step in proof:
            current = (
                _node(step.sibling_hash, current)
                if step.sibling_on_left
                else _node(current, step.sibling_hash)
            )
        return current == root_hash
    except ValueError:
        return False
