from datetime import UTC, datetime, timedelta

import pytest

from app.domain.wallet_auth.quorum import (
    QuorumParticipantType,
    VerifiedQuorumApproval,
)
from app.domain.wallet_auth.quorum import QuorumProofMethod, QuorumType


def test_legacy_and_lnurl_methods_do_not_gain_treasury_or_sovereign_authority() -> None:
    assert QuorumProofMethod.LEGACY_MESSAGE_SIGNATURE.value == "legacy_message_signature"
    assert QuorumProofMethod.LNURL_AUTH.value == "lnurl_auth"
    assert QuorumType.SOVEREIGN.value == "sovereign"


def test_raw_wallet_identifier_cannot_enter_quorum_approval() -> None:
    now = datetime.now(UTC)
    with pytest.raises(ValueError, match="unsafe_quorum_principal_hash"):
        VerifiedQuorumApproval(
            "sha256:approval",
            QuorumParticipantType.BITCOIN_WALLET_PRINCIPAL,
            QuorumParticipantType.BITCOIN_WALLET_PRINCIPAL,
            "bc1qrawaddress",
            "sha256:key",
            QuorumProofMethod.BIP322,
            "sha256:proof",
            "high_assurance",
            now.isoformat(),
            (now + timedelta(minutes=5)).isoformat(),
            "sha256:intent",
            "treasury_policy_change",
            "sha256:policy",
        )
