from pydantic import BaseModel


class HealthOut(BaseModel):
    status: str
    app: str
