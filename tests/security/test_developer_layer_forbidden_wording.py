from pathlib import Path

FORBIDDEN = (
    "clean address",
    "dirty address",
    "criminal address",
    "guaranteed safe",
    "approved payment",
    "verified illicit",
    "risk-free",
    "legally verified",
    "consensus verified",
    "custody-ready",
    "auto-approved transaction",
)
SEARCH_ROOTS = [
    Path("app/events"),
    Path("app/services/events"),
    Path("sdk"),
    Path("cli"),
    Path("mcp"),
    Path("app/plugins"),
    Path("docs"),
]


def test_developer_layer_forbidden_wording_absent() -> None:
    offenders: list[str] = []
    for root in SEARCH_ROOTS:
        for path in root.rglob("*"):
            if path.name.endswith("safety.py"):
                continue
            if path.is_file() and path.suffix in {".py", ".md", ".ts", ".tsx"}:
                text = path.read_text(encoding="utf-8", errors="ignore").casefold()
                for phrase in FORBIDDEN:
                    if phrase in text:
                        offenders.append(f"{path}:{phrase}")
    assert offenders == []
