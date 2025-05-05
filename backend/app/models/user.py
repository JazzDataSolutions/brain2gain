from __future__ import annotations
from typing import List, Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

from .role import UserRoleLink, Role

class User(SQLModel, table=True):
    user_id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, nullable=False, unique=True)
    email: str = Field(index=True, nullable=False, unique=True)
    hashed_password: str = Field(nullable=False)
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    
    roles: List[Role] = Relationship(back_populates="users", link_model=UserRoleLink)

