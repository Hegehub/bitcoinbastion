from datetime import UTC, datetime

from app.services.lnurl.verification_sources import test_bolt11 as make_test_bolt11
from app.services.lnurl.withdraw_invoice_validator import LNURLWithdrawInvoiceValidationRequest, LNURLWithdrawInvoiceValidator


def invoice(amount=1000, network="bitcoin-testnet", expires=600, payment_hash="p"):
    return make_test_bolt11(payment_hash=payment_hash, amount_msat=amount, network=network, timestamp=datetime.now(UTC), expiry_seconds=expires)


def test_valid_invoice_and_mismatch_cases():
    validator = LNURLWithdrawInvoiceValidator()
    ok = validator.validate(LNURLWithdrawInvoiceValidationRequest(invoice(), "bitcoin-testnet", 1000))
    assert ok.allowed and ok.invoice_hash and ok.payment_hash_hash
    assert not validator.validate(LNURLWithdrawInvoiceValidationRequest(invoice(network="bitcoin-mainnet"), "bitcoin-testnet", 1000)).allowed
    assert not validator.validate(LNURLWithdrawInvoiceValidationRequest(invoice(amount=2000), "bitcoin-testnet", 1000)).allowed
    assert not validator.validate(LNURLWithdrawInvoiceValidationRequest(invoice(expires=-1), "bitcoin-testnet", 1000)).allowed


def test_duplicate_and_zero_amount_invoices_rejected():
    validator = LNURLWithdrawInvoiceValidator()
    inv = invoice(payment_hash="dup")
    first = validator.validate(LNURLWithdrawInvoiceValidationRequest(inv, "bitcoin-testnet", 1000))
    assert not validator.validate(LNURLWithdrawInvoiceValidationRequest(inv, "bitcoin-testnet", 1000, used_invoice_hashes=frozenset({first.invoice_hash}))).allowed
    assert not validator.validate(LNURLWithdrawInvoiceValidationRequest(invoice(amount=0), "bitcoin-testnet", 0)).allowed
