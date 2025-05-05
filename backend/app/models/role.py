from __future__ import annotations

from enum import Enum
from typing import List, Optional
from sqlmodel import SQLModel, Field, Relationship

class UserRoleEnum(str, Enum):
    ADMIN      = "ADMIN"
    MANAGER    = "MANAGER"
    SELLER     = "SELLER"
    ACCOUNTANT = "ACCOUNTANT"

class UserRoleLink(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, foreign_key="user.user_id", primary_key=True)
    role_id: Optional[int] = Field(default=None, foreign_key="role.role_id", primary_key=True)

class Role(SQLModel, table=True):
    role_id: Optional[int] = Field(default=None, primary_key=True)
    name: UserRoleEnum = Field(sa_column_kwargs={"unique": True}, nullable=False)
    users: List["User"] = Relationship(back_populates="roles", link_model=UserRoleLink)

