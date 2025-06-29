"""
Integration tests for Email Template API endpoints
Tests the full email template system including API routes, service integration, and MJML compilation
"""

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock

from app.main import app
from app.services.email_template_service import email_template_service


class TestEmailTemplateIntegration:
    """Integration test suite for Email Template system"""

    @pytest.fixture
    async def client(self):
        """Create test client"""
        async with AsyncClient(app=app, base_url="http://test") as ac:
            yield ac

    @pytest.fixture
    def admin_headers(self):
        """Mock admin authentication headers"""
        # In a real test, you would create a proper admin token
        return {"Authorization": "Bearer mock_admin_token"}

    @pytest.mark.asyncio
    async def test_health_endpoint_public(self, client):
        """Test email template health endpoint (public access)"""
        response = await client.get("/api/v1/email-templates/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "email_template_service"
        assert "templates_available" in data
        assert data["templates_available"] >= 3

    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test that email template service initializes correctly"""
        # Test service is properly initialized
        assert email_template_service.template_dir.exists()
        assert email_template_service.cache_dir.exists()
        
        # Test can list templates
        templates = await email_template_service.list_available_templates()
        assert isinstance(templates, list)
        assert len(templates) >= 3
        assert "order_confirmation" in templates

    @pytest.mark.asyncio
    async def test_template_compilation_integration(self):
        """Test end-to-end template compilation"""
        sample_data = {
            "project_name": "Brain2Gain",
            "customer_name": "Integration Test User",
            "order_id": "INT-TEST-001",
            "order_date": "29 de Junio, 2025",
            "total_amount": "199.99",
            "payment_method": "Tarjeta de Crédito",
            "subtotal": "189.99",
            "shipping_cost": "10.00",
            "order_items": [
                {
                    "product_name": "Proteína Whey Integration Test",
                    "quantity": 2,
                    "unit_price": "89.99",
                    "total_price": "179.98"
                }
            ],
            "shipping_address": {
                "full_name": "Integration Test User",
                "street": "Integration Street 123",
                "city": "Test City",
                "state": "TEST",
                "zip_code": "12345",
                "country": "México"
            },
            "track_order_url": "https://brain2gain.com/orders/INT-TEST-001"
        }
        
        # Test order confirmation compilation
        html = await email_template_service.compile_template("order_confirmation", sample_data)
        
        assert isinstance(html, str)
        assert len(html) > 1000  # Should be substantial content
        assert "Integration Test User" in html
        assert "INT-TEST-001" in html
        assert "199.99" in html
        assert "Proteína Whey Integration Test" in html

    @pytest.mark.asyncio
    async def test_notification_service_email_template_integration(self):
        """Test integration between NotificationService and EmailTemplateService"""
        from app.services.notification_service import NotificationService, NotificationType, NotificationTemplate
        from unittest.mock import AsyncMock
        
        # Mock session
        mock_session = AsyncMock()
        notification_service = NotificationService(mock_session)
        
        # Test data
        order_data = {
            "project_name": "Brain2Gain",
            "customer_name": "Notification Integration Test",
            "order_id": "NIT-001",
            "order_date": "29 de Junio, 2025",
            "total_amount": "89.99",
            "payment_method": "Tarjeta de Crédito",
            "subtotal": "79.99",
            "shipping_cost": "10.00",
            "order_items": [
                {
                    "product_name": "Test Product",
                    "quantity": 1,
                    "unit_price": "79.99",
                    "total_price": "79.99"
                }
            ],
            "shipping_address": {
                "full_name": "Notification Integration Test",
                "street": "Test Street 123",
                "city": "Test City",
                "state": "TEST",
                "zip_code": "12345",
                "country": "México"
            },
            "track_order_url": "https://brain2gain.com/orders/NIT-001"
        }
        
        # Send notification using template
        result = await notification_service.send_notification(
            recipient="integration.test@brain2gain.com",
            notification_type=NotificationType.EMAIL,
            template=NotificationTemplate.ORDER_CONFIRMATION,
            data=order_data
        )
        
        assert result["success"] is True
        assert result["status"].value == "SENT"
        assert "template_used" in result
        assert result["template_used"] == "order_confirmation"

    @pytest.mark.asyncio
    async def test_template_validation_integration(self):
        """Test template validation across multiple templates"""
        templates_to_test = ["order_confirmation", "order_shipped", "order_delivered"]
        
        for template_name in templates_to_test:
            validation_result = await email_template_service.validate_template(template_name)
            
            assert validation_result["valid"] is True
            assert validation_result["template_name"] == template_name
            assert len(validation_result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_cache_functionality_integration(self):
        """Test caching functionality end-to-end"""
        sample_data = {
            "project_name": "Brain2Gain",
            "customer_name": "Cache Test User",
            "order_id": "CACHE-001",
            "order_date": "29 de Junio, 2025",
            "total_amount": "99.99",
            "payment_method": "Tarjeta de Crédito",
            "subtotal": "89.99",
            "shipping_cost": "10.00",
            "order_items": [{"product_name": "Test", "quantity": 1, "unit_price": "89.99", "total_price": "89.99"}],
            "shipping_address": {
                "full_name": "Cache Test User",
                "street": "Cache Street 123",
                "city": "Test City",
                "state": "TEST",
                "zip_code": "12345",
                "country": "México"
            },
            "track_order_url": "https://brain2gain.com/orders/CACHE-001"
        }
        
        # First compilation
        html1 = await email_template_service.compile_template("order_confirmation", sample_data)
        
        # Second compilation (should use cache)
        html2 = await email_template_service.compile_template("order_confirmation", sample_data)
        
        # Should be identical
        assert html1 == html2
        assert len(html1) > 1000
        
        # Clear cache
        cache_cleared = await email_template_service.clear_cache("order_confirmation")
        assert cache_cleared is True
        
        # Third compilation (should recompile)
        html3 = await email_template_service.compile_template("order_confirmation", sample_data)
        assert html3 == html1  # Content should be the same

    @pytest.mark.asyncio
    async def test_multiple_template_compilation(self):
        """Test compiling multiple different templates"""
        base_data = {
            "project_name": "Brain2Gain",
            "customer_name": "Multi Template Test",
            "order_id": "MULTI-001",
            "order_date": "29 de Junio, 2025",
            "total_amount": "99.99",
            "payment_method": "Tarjeta de Crédito",
            "subtotal": "89.99",
            "shipping_cost": "10.00",
            "order_items": [{"product_name": "Test", "quantity": 1, "unit_price": "89.99", "total_price": "89.99"}],
            "shipping_address": {
                "full_name": "Multi Template Test",
                "street": "Multi Street 123",
                "city": "Test City",
                "state": "TEST",
                "zip_code": "12345",
                "country": "México"
            },
            "track_order_url": "https://brain2gain.com/orders/MULTI-001",
            "tracking_number": "1Z999AA1234567890",
            "carrier_name": "FedEx",
            "shipped_date": "30 de Junio, 2025",
            "estimated_delivery": "2 de Julio, 2025",
            "tracking_url": "https://fedex.com/track",
            "delivered_date": "2 de Julio, 2025",
            "delivered_time": "15:30",
            "delivery_address": "Multi Street 123",
            "review_url": "https://brain2gain.com/review/MULTI-001",
            "reorder_url": "https://brain2gain.com/reorder/MULTI-001"
        }
        
        templates = ["order_confirmation", "order_shipped", "order_delivered"]
        compiled_templates = {}
        
        for template_name in templates:
            html = await email_template_service.compile_template(template_name, base_data)
            compiled_templates[template_name] = html
            
            assert isinstance(html, str)
            assert len(html) > 500
            assert "Multi Template Test" in html
            assert "MULTI-001" in html
        
        # Each template should be different
        assert compiled_templates["order_confirmation"] != compiled_templates["order_shipped"]
        assert compiled_templates["order_shipped"] != compiled_templates["order_delivered"]
        assert compiled_templates["order_confirmation"] != compiled_templates["order_delivered"]

    @pytest.mark.asyncio
    async def test_template_error_handling_integration(self):
        """Test error handling in template system"""
        # Test with missing template
        with pytest.raises(ValueError, match="Template compilation failed"):
            await email_template_service.compile_template("nonexistent_template", {})
        
        # Test with incomplete data (should not raise error but handle gracefully)
        incomplete_data = {"customer_name": "Error Test User"}
        
        # Most templates require more data, but the service should handle it gracefully
        try:
            html = await email_template_service.compile_template("order_confirmation", incomplete_data)
            # If it doesn't raise an error, it should still produce some HTML
            assert isinstance(html, str)
        except ValueError as e:
            # If it does raise an error, it should be a template compilation error
            assert "Template compilation failed" in str(e)

    @pytest.mark.asyncio
    async def test_sample_data_consistency(self):
        """Test that sample data generates consistent results"""
        templates = ["order_confirmation", "order_shipped", "order_delivered"]
        
        for template_name in templates:
            # Get sample data
            sample_data = email_template_service._get_sample_data(template_name)
            
            # Compile template with sample data
            html = await email_template_service.compile_template(template_name, sample_data)
            
            assert isinstance(html, str)
            assert len(html) > 500
            
            # Check that basic template-specific content is present
            if template_name == "order_confirmation":
                assert "confirmado" in html.lower() or "confirmed" in html.lower()
            elif template_name == "order_shipped":
                assert "enviado" in html.lower() or "shipped" in html.lower()
            elif template_name == "order_delivered":
                assert "entregado" in html.lower() or "delivered" in html.lower()

    @pytest.mark.asyncio
    async def test_concurrent_template_requests(self):
        """Test handling of concurrent template compilation requests"""
        import asyncio
        
        sample_data = email_template_service._get_sample_data("order_confirmation")
        
        # Create multiple concurrent compilation requests
        tasks = []
        for i in range(5):
            task = email_template_service.compile_template("order_confirmation", sample_data)
            tasks.append(task)
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks)
        
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            assert result == first_result
        
        assert len(first_result) > 1000