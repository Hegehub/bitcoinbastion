"""LNURL successAction domain enums."""

from __future__ import annotations

from enum import StrEnum


class LNURLSuccessActionType(StrEnum):
    MESSAGE = "message"
    URL = "url"
