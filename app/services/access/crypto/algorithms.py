"""Stable algorithm and capability identifiers for Bastion issuer metadata."""

from enum import StrEnum


class SignatureAlgorithm(StrEnum):
    ED25519 = "ed25519"
    ECDSA_SECP256K1 = "ecdsa_secp256k1"
    ML_DSA_44 = "ml_dsa_44"
    ML_DSA_65 = "ml_dsa_65"
    ML_DSA_87 = "ml_dsa_87"
    SLH_DSA_128S = "slh_dsa_128s"
    SLH_DSA_128F = "slh_dsa_128f"
    SLH_DSA_192S = "slh_dsa_192s"
    SLH_DSA_192F = "slh_dsa_192f"
    SLH_DSA_256S = "slh_dsa_256s"
    SLH_DSA_256F = "slh_dsa_256f"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


class HashAlgorithm(StrEnum):
    SHA256 = "sha256"
    SHA3_256 = "sha3_256"
    SHA3_512 = "sha3_512"
    SHAKE128 = "shake128"
    SHAKE256 = "shake256"
    UNKNOWN = "unknown"


class EncryptionOrKEMAlgorithm(StrEnum):
    NONE = "none"
    X25519 = "x25519"
    ML_KEM_512 = "ml_kem_512"
    ML_KEM_768 = "ml_kem_768"
    ML_KEM_1024 = "ml_kem_1024"
    HYBRID_X25519_ML_KEM_768 = "hybrid_x25519_ml_kem_768"
    UNSUPPORTED = "unsupported"
    UNKNOWN = "unknown"


class CryptoCapabilityStatus(StrEnum):
    ACTIVE = "active"
    VERIFY_ONLY = "verify_only"
    SIGN_AND_VERIFY = "sign_and_verify"
    METADATA_ONLY = "metadata_only"
    PLANNED = "planned"
    DISABLED = "disabled"
    DEPRECATED = "deprecated"
    UNSUPPORTED = "unsupported"


class CryptoAssuranceLevel(StrEnum):
    CLASSICAL = "classical"
    CLASSICAL_HARDWARE_BACKED = "classical_hardware_backed"
    HYBRID_TRANSITION = "hybrid_transition"
    POST_QUANTUM = "post_quantum"
    LONG_TERM_ROOT = "long_term_root"
    SOVEREIGN = "sovereign"


PQ_SIGNATURE_ALGORITHMS = frozenset(
    {
        SignatureAlgorithm.ML_DSA_44,
        SignatureAlgorithm.ML_DSA_65,
        SignatureAlgorithm.ML_DSA_87,
        SignatureAlgorithm.SLH_DSA_128S,
        SignatureAlgorithm.SLH_DSA_128F,
        SignatureAlgorithm.SLH_DSA_192S,
        SignatureAlgorithm.SLH_DSA_192F,
        SignatureAlgorithm.SLH_DSA_256S,
        SignatureAlgorithm.SLH_DSA_256F,
    }
)
