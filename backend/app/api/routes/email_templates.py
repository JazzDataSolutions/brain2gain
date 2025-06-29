"""
Email Templates API Routes
Provides endpoints for email template management, preview, and testing
"""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import get_current_active_superuser
from app.core.db import get_session
from app.services.email_template_service import email_template_service
from app.services.notification_service import NotificationService, NotificationType, NotificationTemplate

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[str])
async def list_email_templates(
    current_user: Any = Depends(get_current_active_superuser),
) -> List[str]:
    """
    List all available email templates.
    Admin only endpoint.
    """
    try:
        templates = await email_template_service.list_available_templates()
        return templates
    except Exception as e:
        logger.error(f"Failed to list email templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to list email templates")


@router.get("/{template_name}/preview", response_class=HTMLResponse)
async def preview_email_template(
    template_name: str,
    current_user: Any = Depends(get_current_active_superuser),
) -> HTMLResponse:
    """
    Preview email template with sample data.
    Returns compiled HTML for browser display.
    Admin only endpoint.
    """
    try:
        html_content = await email_template_service.get_template_preview(template_name)
        return HTMLResponse(content=html_content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
    except Exception as e:
        logger.error(f"Failed to preview template {template_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate template preview")


@router.post("/{template_name}/compile", response_model=Dict[str, Any])
async def compile_email_template(
    template_name: str,
    template_data: Dict[str, Any],
    current_user: Any = Depends(get_current_active_superuser),
) -> Dict[str, Any]:
    """
    Compile email template with custom data.
    Returns compiled HTML and metadata.
    Admin only endpoint.
    """
    try:
        html_content = await email_template_service.compile_template(
            template_name, template_data, force_recompile=True
        )
        
        return {
            "template_name": template_name,
            "compiled_html": html_content,
            "data_used": template_data,
            "status": "success",
            "compiled_at": "2025-06-28T10:00:00Z"  # Should use actual datetime
        }
        
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Template '{template_name}' not found")
    except Exception as e:
        logger.error(f"Failed to compile template {template_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to compile template")


@router.get("/{template_name}/validate", response_model=Dict[str, Any])
async def validate_email_template(
    template_name: str,
    current_user: Any = Depends(get_current_active_superuser),
) -> Dict[str, Any]:
    """
    Validate email template structure and compilation.
    Admin only endpoint.
    """
    try:
        validation_result = await email_template_service.validate_template(template_name)
        return validation_result
    except Exception as e:
        logger.error(f"Failed to validate template {template_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to validate template")


@router.post("/{template_name}/test-send")
async def test_send_email_template(
    template_name: str,
    recipient_email: str = Query(..., description="Email address to send test email"),
    custom_data: Dict[str, Any] = None,
    session: AsyncSession = Depends(get_session),
    current_user: Any = Depends(get_current_active_superuser),
) -> Dict[str, Any]:
    """
    Send test email using specified template.
    Admin only endpoint for testing email delivery.
    """
    try:
        # Use custom data or sample data
        template_data = custom_data if custom_data else email_template_service._get_sample_data(template_name)
        
        # Map template name to NotificationTemplate enum
        template_mapping = {
            "order_confirmation": NotificationTemplate.ORDER_CONFIRMATION,
            "order_shipped": NotificationTemplate.ORDER_SHIPPED,
            "order_delivered": NotificationTemplate.ORDER_DELIVERED,
            "reset_password": NotificationTemplate.PASSWORD_RESET,
            "new_account": NotificationTemplate.ACCOUNT_CREATED,
        }
        
        notification_template = template_mapping.get(template_name)
        if not notification_template:
            raise HTTPException(
                status_code=400, 
                detail=f"Template '{template_name}' is not mapped to a notification template"
            )
        
        # Create notification service and send test email
        notification_service = NotificationService(session)
        
        result = await notification_service.send_notification(
            recipient=recipient_email,
            notification_type=NotificationType.EMAIL,
            template=notification_template,
            data=template_data,
            metadata={"test_send": True, "admin_user": current_user.email}
        )
        
        return {
            "template_name": template_name,
            "recipient": recipient_email,
            "notification_result": result,
            "template_data": template_data,
            "status": "sent" if result.get("success") else "failed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send test email for template {template_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to send test email")


@router.delete("/cache", response_model=Dict[str, Any])
async def clear_template_cache(
    template_name: str = Query(None, description="Specific template to clear cache for"),
    current_user: Any = Depends(get_current_active_superuser),
) -> Dict[str, Any]:
    """
    Clear email template compilation cache.
    Admin only endpoint.
    """
    try:
        success = await email_template_service.clear_cache(template_name)
        
        return {
            "success": success,
            "message": f"Cache cleared for {'all templates' if not template_name else template_name}",
            "template_name": template_name
        }
        
    except Exception as e:
        logger.error(f"Failed to clear template cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear template cache")


@router.get("/sample-data/{template_name}", response_model=Dict[str, Any])
async def get_template_sample_data(
    template_name: str,
    current_user: Any = Depends(get_current_active_superuser),
) -> Dict[str, Any]:
    """
    Get sample data structure for a template.
    Useful for understanding template variables and testing.
    Admin only endpoint.
    """
    try:
        sample_data = email_template_service._get_sample_data(template_name)
        
        return {
            "template_name": template_name,
            "sample_data": sample_data,
            "data_fields": list(sample_data.keys()),
            "description": f"Sample data structure for {template_name} template"
        }
        
    except Exception as e:
        logger.error(f"Failed to get sample data for template {template_name}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get sample data")


@router.get("/health", response_model=Dict[str, Any])
async def email_template_health_check() -> Dict[str, Any]:
    """
    Health check for email template service.
    Returns service status and available templates count.
    """
    try:
        templates = await email_template_service.list_available_templates()
        
        return {
            "status": "healthy",
            "service": "email_template_service",
            "templates_available": len(templates),
            "templates": templates,
            "template_directory": str(email_template_service.template_dir),
            "cache_directory": str(email_template_service.cache_dir)
        }
        
    except Exception as e:
        logger.error(f"Email template service health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "email_template_service",
            "error": str(e)
        }