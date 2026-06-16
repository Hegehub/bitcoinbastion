from __future__ import annotations

from bastion_ui.components.ui.alert import alert
from bastion_ui.components.ui.badge import badge
from bastion_ui.components.ui.button import button
from bastion_ui.components.ui.card import card
from bastion_ui.components.ui.empty_state import empty_state
from bastion_ui.components.ui.input import input_field
from bastion_ui.components.ui.metric import metric_card
from bastion_ui.components.ui.skeleton import skeleton
from bastion_ui.components.ui.table import table


def test_ui_components_import_and_render_objects() -> None:
    assert button("Action") is not None
    assert card(title="Card") is not None
    assert badge("Advisory") is not None
    assert alert("Manual review recommended.") is not None
    assert input_field("Label") is not None
    assert table(["A"], [["B"]]) is not None
    assert metric_card("Label", "Value") is not None
    assert skeleton("card") is not None
    assert empty_state("Empty", "Nothing to show yet.") is not None
