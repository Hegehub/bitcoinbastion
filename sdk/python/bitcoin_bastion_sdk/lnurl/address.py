from __future__ import annotations

import ipaddress
import re
from urllib.parse import quote

_ADDRESS = re.compile(r"^(?P<name>[A-Za-z0-9._-]{1,64})@(?P<domain>[A-Za-z0-9.-]{1,253})$")


def lightning_address_path(address: str) -> str:
    match = _ADDRESS.fullmatch(address.strip())
    if not match:
        raise ValueError("Invalid Lightning Address")
    domain = match.group("domain").lower().rstrip(".")
    try:
        ipaddress.ip_address(domain)
    except ValueError:
        pass
    else:
        raise ValueError("Lightning Address must use a trusted DNS domain")
    return f"https://{domain}/.well-known/lnurlp/{quote(match.group('name'), safe='')}"
