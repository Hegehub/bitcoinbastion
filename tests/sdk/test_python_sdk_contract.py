import sys
from pathlib import Path

sys.path.insert(0, str(Path("sdk/python").resolve()))

import inspect

from bitcoin_bastion_sdk.client import BastionClient
from bitcoin_bastion_sdk.errors import (
    BastionAPIError,
    BastionAuthError,
    BastionNotFoundError,
    BastionRateLimitError,
    BastionTimeoutError,
    BastionValidationError,
)
from bitcoin_bastion_sdk.safety import SAFETY_MESSAGE, assert_safe


def test_python_sdk_exposes_timeout_and_safety_helpers() -> None:
    client = BastionClient(base_url="http://localhost:8000", timeout=3.0)
    assert client._transport.config.timeout == 3.0
    assert "Never submit seed phrases" in SAFETY_MESSAGE
    assert "BastionSafetyError" in inspect.getsource(assert_safe)


def test_python_sdk_error_classes_exist_for_common_http_statuses() -> None:
    assert issubclass(BastionValidationError, BastionAPIError)
    assert issubclass(BastionAuthError, BastionAPIError)
    assert issubclass(BastionNotFoundError, BastionAPIError)
    assert issubclass(BastionRateLimitError, BastionAPIError)
    assert issubclass(BastionTimeoutError, Exception)
