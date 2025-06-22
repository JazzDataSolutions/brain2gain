import uuid
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
    session: SessionDep,
    token: TokenDep,
) -> User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        token_data = TokenPayload(**payload)
    except (InvalidTokenError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials"
        )

    try:
        # Convert string ID to UUID for database lookup
        user_id = uuid.UUID(str(token_data.sub))
        user = await session.get(User, user_id)
    except (ValueError, TypeError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid token format"
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return user

CurrentUser = Annotated[User, Depends(get_current_user)]

def get_current_active_superuser(current_user: CurrentUser) -> User:
    """Allow only superusers."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="The user doesn't have enough privileges"
        )
    return current_user

def get_current_admin_user(current_user: CurrentUser) -> User:
    """Allow only users with ADMIN or MANAGER roles or superuser."""
    if current_user.is_superuser:
        return current_user

    role_names = {role.name for role in current_user.roles}
    allowed_roles = {"ADMIN", "MANAGER"}

    if role_names & allowed_roles:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User does not have admin privileges"
    )

def get_current_seller_user(current_user: CurrentUser) -> User:
    """Allow users with ADMIN, MANAGER, or SELLER roles or superuser."""
    if current_user.is_superuser:
        return current_user

    role_names = {role.name for role in current_user.roles}
    allowed_roles = {"ADMIN", "MANAGER", "SELLER"}

    if role_names & allowed_roles:
        return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="User does not have seller privileges"
    )

# Type annotations for dependencies
AdminUser = Annotated[User, Depends(get_current_admin_user)]
SellerUser = Annotated[User, Depends(get_current_seller_user)]
SuperUser = Annotated[User, Depends(get_current_active_superuser)]

