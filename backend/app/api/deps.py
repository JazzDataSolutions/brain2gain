from typing import Annotated
import jwt

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError
from pydantic import ValidationError
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core import security
from app.core.config import settings
from app.core.database import get_db
from app.models import TokenPayload, User

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/login/access-token")

SessionDep = Annotated[AsyncSession, Depends(get_db)]
TokenDep   = Annotated[str, Depends(reusable_oauth2)]

async def get_current_user(
    session: AsyncSession = Depends(get_db),
    token: str = Depends(reusable_oauth2),
) -> User:
    try:
        payload    = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="Could not validate credentials")
    user = await session.get(User, token_data.sub)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]

def get_current_active_superuser(current_user: CurrentUser) -> User:
    """Allow only superusers."""
    if not current_user.is_superuser:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="The user doesn't have enough privileges")
    return current_user

async def get_current_admin_user(current_user: CurrentUser) -> User:
    """Allow only ADMIN/MANAGER roles or superuser."""
    roles   = {r.name for r in current_user.roles}
    allowed = {"ADMIN", "MANAGER"}
    if current_user.is_superuser or roles & allowed:
        return current_user
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail="User does not have admin privileges")



async def get_current_admin_user(current_user: CurrentUser) -> User:
    """Allow only users with ADMIN or MANAGER roles or superuser."""
    role_names = {role.name for role in current_user.roles}
    allowed = {"ADMIN", "MANAGER"}
    if current_user.is_superuser or role_names & allowed:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User does not have admin privileges"
    )


async def get_current_admin_user(current_user: CurrentUser) -> User:
    """Allow only users with ADMIN or MANAGER roles or superuser."""
    role_names = {role.name for role in current_user.roles}
    allowed = {"ADMIN", "MANAGER"}
    if current_user.is_superuser or role_names & allowed:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User does not have admin privileges"
    )

async def get_current_admin_user(current_user: CurrentUser) -> User:
    """Allow only users with ADMIN or MANAGER roles or superuser."""
    role_names = {role.name for role in current_user.roles}
    allowed = {"ADMIN", "MANAGER"}
    if current_user.is_superuser or role_names & allowed:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User does not have admin privileges"
    )

async def get_current_admin_user(current_user: CurrentUser) -> User:
    """Allow only users with ADMIN or MANAGER roles or superuser."""
    role_names = {role.name for role in current_user.roles}
    allowed = {"ADMIN", "MANAGER"}
    if current_user.is_superuser or role_names & allowed:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User does not have admin privileges"
    )

