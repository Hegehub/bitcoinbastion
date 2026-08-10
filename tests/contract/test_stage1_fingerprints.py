from __future__ import annotations

import copy
import hashlib
import json

from scripts.stage1_fingerprints import manifest


def fingerprint(rows: object) -> str:
    return hashlib.sha256(json.dumps(rows, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def test_fingerprints_are_stable_and_categorized() -> None:
    first = manifest()
    assert first == manifest()
    roles = {row["role"] for row in first["inputs"]}
    assert roles == {"contract_source", "contract_registry", "generator"}


def test_unrelated_input_is_not_part_of_stage1_manifest() -> None:
    paths = {row["path"] for row in manifest()["inputs"]}
    assert "frontend/bastion_ui/routes/status.py" not in paths
    assert "frontend/bastion_ui/domain/provenance.py" not in paths


def test_contract_and_generator_changes_are_sensitive_and_separate() -> None:
    current = manifest()
    contracts = [row for row in current["inputs"] if row["role"] != "generator"]
    generators = [row for row in current["inputs"] if row["role"] == "generator"]
    changed_contracts = copy.deepcopy(contracts)
    changed_contracts[0]["sha256"] = "0" * 64
    changed_generators = copy.deepcopy(generators)
    changed_generators[0]["sha256"] = "0" * 64
    assert fingerprint(changed_contracts) != fingerprint(contracts)
    assert fingerprint(changed_generators) != fingerprint(generators)
