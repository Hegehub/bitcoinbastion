from pydantic import BaseModel


class CreateNewsSourceRequest(BaseModel):
    name: str
    slug: str
    kind: str
    base_url: str = ""


class NewsSourceResponse(BaseModel):
    id: int
    name: str
    slug: str
    is_active: bool = True
