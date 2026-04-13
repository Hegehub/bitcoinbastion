from pydantic import BaseModel, EmailStr


class UserOut(BaseModel):
    id: int
    email: EmailStr
    username: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}
