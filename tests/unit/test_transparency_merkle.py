from app.services.access.crypto.hashing import sha256_prefixed
from app.services.wallet_auth.transparency.merkle import (
    build_merkle_proof, build_merkle_root, deterministic_empty_root, verify_merkle_proof,
)


def test_merkle_vectors_and_proofs_are_deterministic():
    leaves = [sha256_prefixed(value) for value in ("a", "b", "c")]
    root = build_merkle_root(leaves)
    ordered = sorted(leaves)
    proof = build_merkle_proof(leaves, 1)
    assert root == build_merkle_root(list(reversed(leaves)))
    assert verify_merkle_proof(ordered[1], proof, root)
    assert not verify_merkle_proof(sha256_prefixed("tampered"), proof, root)
    assert build_merkle_root([]) == deterministic_empty_root()
    assert build_merkle_root(leaves + [leaves[-1]]) != root


def test_leaf_and_node_domains_do_not_collide():
    digest = sha256_prefixed("a")
    assert build_merkle_root([digest]) == digest
    assert build_merkle_root([digest, digest]) != digest
