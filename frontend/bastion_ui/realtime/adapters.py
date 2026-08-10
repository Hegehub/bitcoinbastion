from __future__ import annotations

from bastion_ui.domain.provenance import Provenance
from bastion_ui.realtime.contracts import SystemFrame
from bastion_ui.realtime.models import StreamStatusViewModel


def adapt_connection_accepted(frame: SystemFrame, provenance: Provenance) -> StreamStatusViewModel:
    if frame.event_type != "connection.accepted" or frame.stream is None:
        raise ValueError("connection_accepted_frame_required")
    return StreamStatusViewModel(
        stream=frame.stream,
        message=frame.message,
        topics=tuple(frame.topics or ()),
        wire_version=frame.wire_version,
        provenance=provenance,
    )
