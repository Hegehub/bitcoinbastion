from app.schemas.bastion_trace import OperatorNoteType


def sanitize_note_type(note_type: str) -> OperatorNoteType:
    try:
        return OperatorNoteType(note_type)
    except ValueError:
        return OperatorNoteType.GENERAL
