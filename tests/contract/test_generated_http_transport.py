from __future__ import annotations

import inspect
from pathlib import Path
import sys

import pytest
from pydantic import ValidationError as PydanticValidationError

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "frontend"))

from bastion_ui.transport import generated_http, generated_schemas  # noqa: E402


NAMED_MATRIX_IDS = {
    "HTTP-0002",
    "HTTP-0005",
    "HTTP-0010",
    "HTTP-0013",
    "HTTP-0019",
    "HTTP-0020",
    "HTTP-0023",
    "HTTP-0031",
}
PROTECTED_NAMED_IDS = NAMED_MATRIX_IDS - {"HTTP-0023", "HTTP-0031"}


def test_closed_empty_validation_context_is_strict() -> None:
    model = generated_schemas.ValidationError
    base = {"loc": ["body"], "msg": "invalid", "type": "value_error"}
    assert model.model_validate({**base, "ctx": {}}).ctx is not None
    assert model.model_validate(base).ctx is None
    assert model.model_validate({**base, "ctx": None}).ctx is None
    with pytest.raises(PydanticValidationError):
        model.model_validate({**base, "ctx": {"x": 1}})
    with pytest.raises(PydanticValidationError):
        model.model_validate({**base, "ctx": {"anything": None}})


def test_all_active_operations_have_one_owner_and_feature53_entry() -> None:
    assert len(generated_http.OWNERSHIP) == 194
    assert len(generated_http.FEATURE_53) == 194
    assert len(set(generated_http.OWNERSHIP)) == 194
    assert {value[0] for value in generated_http.OWNERSHIP.values()} >= NAMED_MATRIX_IDS
    assert len({entry.registry_id for entry in generated_http.FEATURE_53}) == 194


def test_every_generated_registry_symbol_resolves() -> None:
    for entry in generated_http.FEATURE_53:
        operation_id = entry.operation.operation_id
        matrix_id, module, callable_name = generated_http.OWNERSHIP[operation_id]
        assert matrix_id == entry.operation.matrix_id
        assert module == "bastion_ui.transport.generated_http"
        assert inspect.iscoroutinefunction(getattr(generated_http, callable_name))
        assert getattr(generated_http, entry.request_schema)
        assert getattr(generated_http, entry.success_schema)


def test_access_security_headers_are_transport_injected_not_request_fields() -> None:
    for entry in generated_http.FEATURE_53:
        if entry.operation.matrix_id not in PROTECTED_NAMED_IDS:
            continue
        request = getattr(generated_http, entry.request_schema)
        assert "X_Bastion_Session" not in request.model_fields
        assert entry.operation.security.access_required
        assert not entry.operation.security.public
