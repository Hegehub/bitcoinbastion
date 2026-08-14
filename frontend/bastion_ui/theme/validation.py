"""Deterministic token, contrast, and visual-cost validation."""

from __future__ import annotations

import re
from dataclasses import asdict
from pathlib import Path

from bastion_ui.theme.materials import MATERIALS, validate_materials
from bastion_ui.theme.tokens import DARK, LIGHT, ThemePalette

HEX = re.compile(r"#[0-9A-Fa-f]{6}\b")
REQUIRED = frozenset(ThemePalette.__annotations__)


def _rgb(value: str) -> tuple[float, float, float]:
    return tuple(int(value[i : i + 2], 16) / 255 for i in (1, 3, 5))  # type: ignore[return-value]


def _lum(value: str) -> float:
    vals = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in _rgb(value)]
    return 0.2126 * vals[0] + 0.7152 * vals[1] + 0.0722 * vals[2]


def contrast(a: str, b: str) -> float:
    x, y = sorted((_lum(a), _lum(b)), reverse=True)
    return (x + 0.05) / (y + 0.05)


def validate_visual_system() -> None:
    validate_materials()
    for name, palette in (("dark", DARK), ("light", LIGHT)):
        values = asdict(palette)
        if set(values) != REQUIRED or any(not value for value in values.values()):
            raise ValueError(f"incomplete {name} palette")
        if contrast(palette.text, palette.background) < 7:
            raise ValueError(f"insufficient primary contrast: {name}")
        if contrast(palette.text_secondary, palette.background) < 4.5:
            raise ValueError(f"insufficient secondary contrast: {name}")
    if len([m for m in MATERIALS if "GLASS" in m.value]) > 3:
        raise ValueError("unbounded glass hierarchy")


def visual_inventory(root: Path) -> dict[str, int]:
    texts = [p.read_text(errors="ignore") for p in root.rglob("*.py") if "tests" not in p.parts]
    joined = "\n".join(texts)
    return {
        "python_files": len(texts),
        "hardcoded_hex": len(HEX.findall(joined)),
        "backdrop_filters": joined.count("backdrop_filter"),
        "box_shadows": joined.count("box_shadow"),
        "animations": joined.count('"animation"'),
    }


def canonical_blue_audit(root: Path) -> tuple[str, ...]:
    allowed = {"tokens.py", "validation.py"}  # explicit audit/compatibility references
    return tuple(
        str(p)
        for p in root.rglob("*.py")
        if p.name not in allowed
        and re.search(r"#(?:[0-9A-Fa-f]{2}){3}", p.read_text())
        and "#3B82F6" in p.read_text()
    )
