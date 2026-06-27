from __future__ import annotations

KEYBOARD_EXPECTATIONS = (
    "Tab order is logical.",
    "Shift+Tab returns to prior focusable controls.",
    "Escape closes menus, dialogs, and command palette where state is available.",
    "Enter activates links and buttons.",
    "Space activates button-like controls.",
)


def keyboard_help_text() -> str:
    return " ".join(KEYBOARD_EXPECTATIONS)
