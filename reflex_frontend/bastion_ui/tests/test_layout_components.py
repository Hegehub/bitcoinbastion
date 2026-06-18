from __future__ import annotations

import reflex as rx

from bastion_ui.components.layout.console_layout import console_layout
from bastion_ui.components.layout.container import container
from bastion_ui.components.layout.grid import responsive_grid, three_column_grid, two_column_grid
from bastion_ui.components.layout.public_layout import public_layout
from bastion_ui.components.layout.section import section
from bastion_ui.components.layout.shell import console_shell, page_shell, public_shell
from bastion_ui.components.layout.stack import inline_stack, stack


def test_layout_components_import_and_render_objects() -> None:
    child = rx.text("content")
    assert public_layout(child) is not None
    assert console_layout(child) is not None
    assert page_shell("Title", child) is not None
    assert public_shell(child) is not None
    assert console_shell(child) is not None
    assert container(child) is not None
    assert section(child, title="Section") is not None
    assert responsive_grid(child) is not None
    assert two_column_grid(child) is not None
    assert three_column_grid(child) is not None
    assert stack(child) is not None
    assert inline_stack(child) is not None
