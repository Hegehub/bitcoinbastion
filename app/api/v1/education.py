from fastapi import APIRouter

from app.schemas.base import ResponseEnvelope
from app.schemas.education import EducationSnippetOut
from app.services.education.education_service import EducationService

router = APIRouter(prefix="/education", tags=["education"])


@router.get("/snippets", response_model=ResponseEnvelope[list[EducationSnippetOut]])
def list_snippets() -> ResponseEnvelope[list[EducationSnippetOut]]:
    return ResponseEnvelope(data=EducationService().list_snippets())
