# backend/app/schemas/role.py
from pydantic import BaseModel

from app.models import UserRoleEnum


class RoleRead(BaseModel):
    role_id: int
    name: UserRoleEnum

    model_config = {"from_attributes": True}
