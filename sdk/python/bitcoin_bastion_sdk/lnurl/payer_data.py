from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class LNURLPayerData:
    auth: dict[str, str] | None = None
    identifier: str | None = None
    pubkey: str | None = None
    name: str | None = None
    email: str | None = None

    def as_payload(self) -> dict[str, object]:
        return {key: value for key, value in vars(self).items() if value is not None}
