from pydantic import BaseModel


class EducationSnippetOut(BaseModel):
    slug: str
    title: str
    summary: str
    level: str
