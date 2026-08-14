"""Bounded material hierarchy with readable fallbacks."""

from __future__ import annotations

from bastion_ui.theme.tokens import BLUR, COLOR, SHADOW, MaterialLevel

MATERIALS: dict[MaterialLevel, dict[str, str]] = {
    MaterialLevel.SOLID: {"background": COLOR["surface"]},
    MaterialLevel.MATTE: {"background": COLOR["matte"]},
    MaterialLevel.GLASS_SUBTLE: {
        "background": COLOR["glass"],
        "backdrop_filter": f"blur({BLUR['subtle']}) saturate(1.08)",
    },
    MaterialLevel.GLASS_ELEVATED: {
        "background": COLOR["glass"],
        "backdrop_filter": f"blur({BLUR['elevated']}) saturate(1.1)",
        "box_shadow": SHADOW["medium"],
    },
    MaterialLevel.GLASS_OVERLAY: {
        "background": COLOR["glass"],
        "backdrop_filter": f"blur({BLUR['overlay']}) saturate(1.12)",
        "box_shadow": SHADOW["high"],
    },
}


def material_style(level: MaterialLevel) -> dict[str, str]:
    return {**MATERIALS[level], "border": f"1px solid {COLOR['border']}"}


def validate_materials() -> None:
    if set(MATERIALS) != set(MaterialLevel):
        raise ValueError("material hierarchy is incomplete")
    for level in MaterialLevel:
        if "background" not in MATERIALS[level]:
            raise ValueError(f"material has no readable background: {level}")
