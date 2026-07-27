import inspect

import pytest

from app.services.wallet_auth.transparency import models
from app.services.wallet_auth.transparency.privacy import validate_source_metadata


@pytest.mark.parametrize("field", ["bitcoin_address", "wallet_public_key", "lnurl_key", "raw_k1", "invoice", "preimage", "recovery_file", "mnemonic", "xprv", "session_token", "payment_hash"])
def test_transparency_rejects_sensitive_public_material(field: str):
    with pytest.raises(ValueError):
        validate_source_metadata({"nested": {field: "raw-secret"}}, public_safe=True)


def test_checkpoint_model_has_no_raw_secret_storage_fields():
    source = inspect.getsource(models.TransparencyCheckpoint)
    for forbidden in ("wallet_address", "linking_key", "raw_k1", "invoice", "preimage", "recovery_phrase", "private_key"):
        assert forbidden not in source
