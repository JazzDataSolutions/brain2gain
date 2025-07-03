"""
Authentication routes for nginx auth_request module
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session

from app.api.deps import get_current_user
from app.core.db import get_session
from app.models import User

router = APIRouter()


@router.get("/verify-admin")
async def verify_admin_access(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Verify admin access for nginx auth_request module
    
    This endpoint is used by nginx to verify if a user has admin access
    to protected admin routes. Returns 200 for valid admin users, 
    401/403 for unauthorized users.
    """
    try:
        # Check if user is authenticated
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Check if user is active
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )
        
        # Check if user has admin privileges
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        # Log admin access for audit
        original_uri = request.headers.get("X-Original-URI", "unknown")
        print(f"🔒 Admin access granted: {current_user.email} -> {original_uri}")
        
        # Return success for nginx
        return {"status": "authorized", "user_id": current_user.id}
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log unexpected errors
        print(f"🚨 Admin verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/verify-user")
async def verify_user_access(
    request: Request,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Verify user access for nginx auth_request module
    
    This endpoint verifies if a user is authenticated and active
    for protected user routes.
    """
    try:
        # Check if user is authenticated
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        # Check if user is active
        if not current_user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )
        
        # Return success for nginx
        return {"status": "authorized", "user_id": current_user.id}
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log unexpected errors
        print(f"🚨 User verification error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )