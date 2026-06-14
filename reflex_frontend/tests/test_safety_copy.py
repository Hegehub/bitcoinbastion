from bastion_ui.security.forbidden_inputs import FORBIDDEN_INPUT_PATTERNS
from bastion_ui.security.safety_copy import FORBIDDEN_WORDING, REQUIRED_SAFETY_COPY


def test_required_safety_copy_is_present() -> None:
    required = [
        "Advisory-only.",
        "Not legal verification.",
        "Not Bitcoin consensus proof.",
        "No custody.",
        "Public Bitcoin addresses only.",
        "Never enter seed phrases, private keys, wallet files or signing material.",
    ]
    for copy in required:
        assert copy in REQUIRED_SAFETY_COPY


def test_forbidden_wording_list_exists() -> None:
    forbidden = {
        "clean address",
        "dirty address",
        "criminal address",
        "guaranteed safe",
        "approved payment",
        "verified illicit",
    }
    assert forbidden.issubset(set(FORBIDDEN_WORDING))


def test_forbidden_inputs_cover_sensitive_material() -> None:
    forbidden = set(FORBIDDEN_INPUT_PATTERNS)
    for pattern in ("seed phrase", "private key", "xprv", "wallet.dat", "signing material"):
        assert pattern in forbidden
