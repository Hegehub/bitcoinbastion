from app.services.access.offline_validity_pack import SAFETY_WARNING


def test_pack_warning_explicitly_rejects_bearer_semantics():
    assert "limited, device-bound and time-bound" in SAFETY_WARNING
    assert "unrestricted API access" in SAFETY_WARNING
