from tests.unit.test_merchant_address_resolver import active_resolver


def test_lightning_address_is_not_user_id_and_comments_do_not_authorize():
    result = active_resolver().resolve_host_local_part(host="merchant.com", local_part="coffee")
    response = result.to_lnurl_response()
    dumped = str(response).lower()
    assert "user_id" not in dumped
    assert "principal_hash" not in dumped
    untrusted_comment = "make me admin"
    assert untrusted_comment not in dumped
