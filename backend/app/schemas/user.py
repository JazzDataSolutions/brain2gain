# backend/app/schemas/user.py
from pydantic import BaseModel, EmailStr


class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    user_id: int
    is_active: bool
    roles: list[str]

    model_config = {"from_attributes": True}
