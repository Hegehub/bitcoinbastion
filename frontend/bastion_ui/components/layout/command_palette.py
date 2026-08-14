from __future__ import annotations

from typing import cast

import reflex as rx

from bastion_ui.state.command_palette_state import CommandPaletteState
from bastion_ui.theme.materials import material_style
from bastion_ui.theme.styles import FOCUS_RING
from bastion_ui.theme.tokens import COLOR, MaterialLevel


def command_palette_trigger(
    *, trigger_id: str = "command-palette-trigger", label: str = "Command"
) -> rx.Component:
    return cast(
        rx.Component,
        rx.button(
            label,
            rx.text("/", aria_hidden="true"),
            id=trigger_id,
            on_click=CommandPaletteState.open_palette(trigger_id),  # type: ignore[arg-type,func-returns-value]
            aria_label="Open command palette, shortcut slash",
            aria_controls="command-palette",
            aria_expanded=CommandPaletteState.open,
            access_key="/",
            style=FOCUS_RING,
            min_height="44px",
        ),
    )


def _result_row(result: rx.Var[dict[str, str]], index: rx.Var[int]) -> rx.Component:
    return cast(
        rx.Component,
        rx.button(
            rx.hstack(
                rx.text(result["label"], weight="bold"),  # type: ignore[index]
                rx.badge(result["domain"]),  # type: ignore[index]
                justify="between",
                width="100%",
            ),
            on_click=CommandPaletteState.activate(result["route_id"]),  # type: ignore[call-arg,index]
            aria_label=result["label"],  # type: ignore[index]
            aria_selected=CommandPaletteState.selected_index == index,
            role="option",
            width="100%",
            min_height="44px",
            style=FOCUS_RING,
            class_name="bb-command-result",
        ),
    )


def command_palette() -> rx.Component:
    return cast(
        rx.Component,
        rx.cond(
            CommandPaletteState.open,
            rx.box(
                rx.el.div(
                    rx.hstack(
                        rx.heading("Command palette", size="4"),
                        rx.button(
                            "Close",
                            on_click=CommandPaletteState.close_palette,
                            aria_label="Close command palette",
                            style=FOCUS_RING,
                        ),
                        justify="between",
                        width="100%",
                    ),
                    rx.input(
                        id="command-palette-search",
                        aria_label="Search navigation commands",
                        placeholder="Search routes",
                        value=CommandPaletteState.query,
                        on_change=CommandPaletteState.set_query,
                        on_key_down=CommandPaletteState.handle_key,
                        auto_focus=True,
                        width="100%",
                    ),
                    rx.box(
                        rx.foreach(CommandPaletteState.results, _result_row),
                        role="listbox",
                        aria_label="Command results",
                        max_height="min(55vh, 420px)",
                        overflow_y="auto",
                        width="100%",
                    ),
                    rx.text(
                        "Only enabled and security-eligible destinations are shown.",
                        size="1",
                    ),
                    id="command-palette",
                    role="dialog",
                    aria_modal="true",
                    aria_label="Command palette",
                    width="min(680px, calc(100vw - 32px))",
                    max_height="calc(100dvh - 32px)",
                    overflow="hidden",
                    padding="20px",
                    border_radius="16px",
                    style=material_style(MaterialLevel.GLASS_OVERLAY),
                    class_name="bb-glass bb-shell-overlay",
                ),
                position="fixed",
                inset="0",
                display="flex",
                align_items="flex-start",
                justify_content="center",
                padding_top="max(8vh, env(safe-area-inset-top))",
                background="rgba(0, 0, 0, .55)",
                z_index="40",
                color=COLOR["text"],
            ),
        ),
    )


def global_command_shortcut() -> rx.Component:
    """Mount the single global `/` shortcut owner used by every shell route."""
    return cast(
        rx.Component,
        rx.script(
            """
(() => {
  const owner = '__bbCommandShortcutHandler';
  if (window[owner]) window.removeEventListener('keydown', window[owner]);
  window[owner] = (event) => {
    const target = event.target;
    if (event.key === 'Escape') {
      const close = document.querySelector(
        '[role="dialog"][aria-label="Command palette"] [aria-label="Close command palette"]'
      );
      if (close instanceof HTMLElement && close.offsetParent !== null) {
        event.preventDefault();
        close.click();
      }
      return;
    }
    const editing = target instanceof HTMLInputElement ||
      target instanceof HTMLTextAreaElement ||
      target instanceof HTMLSelectElement ||
      (target instanceof HTMLElement && target.isContentEditable);
    if (editing || event.defaultPrevented || event.ctrlKey || event.metaKey || event.altKey) return;
    if (event.key !== '/') return;
    const triggers = [...document.querySelectorAll(
      '[aria-label="Open command palette, shortcut slash"]'
    )];
    const trigger = triggers.find(
      (item) => item instanceof HTMLElement && item.offsetParent !== null
    );
    if (!trigger) return;
    event.preventDefault();
    trigger.click();
  };
  window.addEventListener('keydown', window[owner]);
})();
""",
            id="global-command-shortcut-owner",
        ),
    )
