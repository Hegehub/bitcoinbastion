import pytest

from bastion_ui.auth_models import PaymentState, PaymentVerification
from bastion_ui.lnurl_safety import validate_payment_comment, validate_success_action_url


def entitlement_active(verification: PaymentVerification) -> bool:
    return verification.settled and verification.entitlement_reference is not None


def test_invoice_issuance_is_not_entitlement_activation() -> None:
    assert PaymentState.INVOICE_ISSUED.value == "invoice_issued"
    pending = PaymentVerification("pay_1", settled=False, entitlement_reference="ent_unsafe")
    assert entitlement_active(pending) is False


def test_settled_payment_requires_backend_entitlement_reference() -> None:
    settled_without_entitlement = PaymentVerification("pay_1", settled=True)
    active = PaymentVerification("pay_1", settled=True, entitlement_reference="ent_1")
    assert entitlement_active(settled_without_entitlement) is False
    assert entitlement_active(active) is True


def test_comment_is_only_bounded_metadata_and_success_url_is_allowlisted() -> None:
    assert validate_payment_comment("note", 4) == "note"
    with pytest.raises(ValueError):
        validate_payment_comment("admin=true", 4)
    assert validate_success_action_url(
        "https://app.bitcoin-bastion.com/activated",
        allowed_domains=frozenset({"app.bitcoin-bastion.com"}),
    )
    for unsafe in (
        "javascript:alert(1)",
        "https://evil.test/",
        "https://app.bitcoin-bastion.com/?session_token=secret",
    ):
        with pytest.raises(ValueError):
            validate_success_action_url(
                unsafe, allowed_domains=frozenset({"app.bitcoin-bastion.com"})
            )
