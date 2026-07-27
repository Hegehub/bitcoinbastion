from dataclasses import replace
from datetime import UTC, datetime, timezone

from app.services.wallet_auth.transparency.canonicalization import (
    canonicalize_transparency_leaf, hash_transparency_leaf, normalize_timestamp,
)
from tests.unit.transparency_helpers import leaf


def test_leaf_canonicalization_is_stable_and_version_sensitive():
    item = leaf()
    assert canonicalize_transparency_leaf(item) == canonicalize_transparency_leaf(item)
    assert hash_transparency_leaf(item) != hash_transparency_leaf(replace(item, object_version=2))


def test_timestamp_normalization_is_deterministic():
    assert normalize_timestamp(datetime(2026, 7, 27, 2, tzinfo=timezone.utc)) == "2026-07-27T02:00:00Z"
    assert normalize_timestamp(datetime(2026, 7, 27, 2, tzinfo=UTC)) == "2026-07-27T02:00:00Z"
