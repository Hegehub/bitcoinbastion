from datetime import datetime

from pydantic import BaseModel


class CreateNewsArticleRequest(BaseModel):
    source_id: int
    title: str
    url: str
    published_at: datetime


class NewsArticleResponse(BaseModel):
    id: int
    source_id: int
    title: str
    is_duplicate: bool = False
