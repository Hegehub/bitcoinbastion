from __future__ import annotations

from typing import Literal, cast

import reflex as rx

from bastion_ui.components.ui.alert import alert

NoticeVariant = Literal["info", "warning", "danger", "degraded", "readonly"]

DEFAULT_NOTICE = "Read-only preview. No custody. Evidence-based. Operator review required. Degraded state visibility is preserved."


def operator_notice(text: str = DEFAULT_NOTICE, variant: NoticeVariant = "readonly") -> rx.Component:
    mapped = "warning" if variant in {"degraded", "readonly"} else variant
    return alert(text, cast(Literal["info", "warning", "danger", "success"], mapped), "Operator Notice")
