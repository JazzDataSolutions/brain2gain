"""
Tests for EmailTemplateService
Tests the MJML email template compilation and management functionality
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import tempfile
import os
from pathlib import Path

from app.services.email_template_service import EmailTemplateService


class TestEmailTemplateService:
    """Test suite for EmailTemplateService"""

    @pytest.fixture
    def email_service(self):
        """Create EmailTemplateService instance for testing"""
        return EmailTemplateService()

    @pytest.fixture
    def sample_template_data(self):
        """Sample data for template compilation testing"""
        return {
            "project_name": "Brain2Gain",
            "customer_name": "Juan Pérez",
            "order_id": "BG-TEST-001",
            "order_date": "28 de Junio, 2025",
            "total_amount": "99.99",
            "payment_method": "Tarjeta de Crédito ****1234",
            "subtotal": "79.99",
            "shipping_cost": "10.00",
            "order_items": [
                {
                    "product_name": "Proteína Whey Test",
                    "quantity": 1,
                    "unit_price": "49.99",
                    "total_price": "49.99"
                }
            ],
            "shipping_address": {
                "full_name": "Juan Pérez",
                "street": "Test Street 123",
                "city": "Test City",
                "state": "TEST",
                "zip_code": "12345",
                "country": "México"
            },
            "track_order_url": "https://brain2gain.com/orders/BG-TEST-001",
            "tracking_number": "1Z999AA1234567890",
            "carrier_name": "FedEx",
            "shipped_date": "29 de Junio, 2025",
            "estimated_delivery": "1 de Julio, 2025",
            "tracking_url": "https://fedex.com/track?number=1Z999AA1234567890",
            "delivered_date": "1 de Julio, 2025",
            "delivered_time": "14:30",
            "delivery_address": "Test Street 123, Test City",
            "review_url": "https://brain2gain.com/review/BG-TEST-001",
            "reorder_url": "https://brain2gain.com/reorder/BG-TEST-001"
        }

    @pytest.mark.asyncio
    async def test_list_available_templates(self, email_service):
        """Test listing available MJML templates"""
        templates = await email_service.list_available_templates()
        
        assert isinstance(templates, list)
        assert len(templates) >= 3  # Should have at least order_confirmation, order_shipped, order_delivered
        assert "order_confirmation" in templates
        assert "order_shipped" in templates
        assert "order_delivered" in templates

    @pytest.mark.asyncio
    async def test_validate_existing_template(self, email_service):
        """Test template validation for existing template"""
        result = await email_service.validate_template("order_confirmation")
        
        assert isinstance(result, dict)
        assert result["valid"] is True
        assert result["template_name"] == "order_confirmation"
        assert "errors" in result
        assert len(result["errors"]) == 0

    @pytest.mark.asyncio
    async def test_validate_nonexistent_template(self, email_service):
        """Test template validation for non-existent template"""
        result = await email_service.validate_template("nonexistent_template")
        
        assert isinstance(result, dict)
        assert result["valid"] is False
        assert "errors" in result
        assert len(result["errors"]) > 0

    @pytest.mark.asyncio
    async def test_compile_template_success(self, email_service, sample_template_data):
        """Test successful template compilation"""
        html = await email_service.compile_template("order_confirmation", sample_template_data)
        
        assert isinstance(html, str)
        assert len(html) > 100  # Should be substantial HTML content
        assert "Juan Pérez" in html  # Customer name should be populated
        assert "BG-TEST-001" in html  # Order ID should be populated
        assert "Brain2Gain" in html  # Project name should be populated

    @pytest.mark.asyncio
    async def test_compile_template_with_cache(self, email_service, sample_template_data):
        """Test template compilation with caching"""
        # First compilation
        html1 = await email_service.compile_template("order_confirmation", sample_template_data)
        
        # Second compilation (should use cache)
        html2 = await email_service.compile_template("order_confirmation", sample_template_data)
        
        assert html1 == html2
        assert len(html1) > 100

    @pytest.mark.asyncio
    async def test_compile_template_force_recompile(self, email_service, sample_template_data):
        """Test template compilation with forced recompilation"""
        html = await email_service.compile_template(
            "order_confirmation", 
            sample_template_data, 
            force_recompile=True
        )
        
        assert isinstance(html, str)
        assert len(html) > 100

    @pytest.mark.asyncio
    async def test_compile_nonexistent_template(self, email_service, sample_template_data):
        """Test compilation of non-existent template raises error"""
        with pytest.raises(ValueError, match="Template compilation failed"):
            await email_service.compile_template("nonexistent_template", sample_template_data)

    @pytest.mark.asyncio
    async def test_get_template_preview(self, email_service):
        """Test template preview generation"""
        html = await email_service.get_template_preview("order_confirmation")
        
        assert isinstance(html, str)
        assert len(html) > 100
        # Should contain sample data
        assert "Juan Test" in html or "Juan Pérez" in html

    @pytest.mark.asyncio
    async def test_clear_cache_all(self, email_service):
        """Test clearing all template cache"""
        result = await email_service.clear_cache()
        
        assert result is True

    @pytest.mark.asyncio
    async def test_clear_cache_specific_template(self, email_service):
        """Test clearing cache for specific template"""
        result = await email_service.clear_cache("order_confirmation")
        
        assert result is True

    def test_get_sample_data_order_confirmation(self, email_service):
        """Test sample data generation for order confirmation"""
        data = email_service._get_sample_data("order_confirmation")
        
        assert isinstance(data, dict)
        assert "customer_name" in data
        assert "order_id" in data
        assert "order_items" in data
        assert "shipping_address" in data
        assert "total_amount" in data

    def test_get_sample_data_order_shipped(self, email_service):
        """Test sample data generation for order shipped"""
        data = email_service._get_sample_data("order_shipped")
        
        assert isinstance(data, dict)
        assert "tracking_number" in data
        assert "carrier_name" in data
        assert "estimated_delivery" in data

    def test_get_sample_data_order_delivered(self, email_service):
        """Test sample data generation for order delivered"""
        data = email_service._get_sample_data("order_delivered")
        
        assert isinstance(data, dict)
        assert "delivered_date" in data
        assert "review_url" in data
        assert "reorder_url" in data

    def test_get_sample_data_unknown_template(self, email_service):
        """Test sample data generation for unknown template returns base data"""
        data = email_service._get_sample_data("unknown_template")
        
        assert isinstance(data, dict)
        assert "project_name" in data
        assert "customer_name" in data
        assert "order_id" in data

    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_mjml_cli_compilation_success(self, mock_subprocess, email_service):
        """Test MJML CLI compilation when available"""
        # Mock successful MJML CLI execution
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = "<html><body>Compiled HTML</body></html>"
        
        html = await email_service._compile_mjml_to_html("<mjml><mj-body>Test</mj-body></mjml>")
        
        assert html == "<html><body>Compiled HTML</body></html>"
        mock_subprocess.assert_called_once()

    @pytest.mark.asyncio
    @patch('subprocess.run')
    async def test_mjml_cli_compilation_failure_fallback(self, mock_subprocess, email_service):
        """Test fallback when MJML CLI fails"""
        # Mock failed MJML CLI execution
        mock_subprocess.return_value.returncode = 1
        mock_subprocess.return_value.stderr = "MJML Error"
        
        html = await email_service._compile_mjml_to_html("<mjml><mj-body>Test</mj-body></mjml>")
        
        # Should fall back to basic conversion
        assert isinstance(html, str)
        assert "Test" in html

    @pytest.mark.asyncio
    async def test_fallback_mjml_to_html(self, email_service):
        """Test fallback MJML to HTML conversion"""
        mjml_content = """
        <mjml>
            <mj-body>
                <mj-section>
                    <mj-column>
                        <mj-text>Hello World</mj-text>
                    </mj-column>
                </mj-section>
            </mj-body>
        </mjml>
        """
        
        html = await email_service._fallback_mjml_to_html(mjml_content)
        
        assert isinstance(html, str)
        assert "Hello World" in html
        assert "<!DOCTYPE html>" in html

    @pytest.mark.asyncio
    async def test_template_compilation_with_missing_variables(self, email_service):
        """Test template compilation with missing variables"""
        incomplete_data = {"customer_name": "Test User"}  # Missing many required fields
        
        # Should not raise error but should compile with missing variables
        html = await email_service.compile_template("order_confirmation", incomplete_data)
        
        assert isinstance(html, str)
        assert "Test User" in html

    @pytest.mark.asyncio
    async def test_template_compilation_error_handling(self, email_service):
        """Test template compilation error handling"""
        # Test with invalid data type
        with pytest.raises(ValueError):
            await email_service.compile_template("order_confirmation", "invalid_data")

    def test_template_directory_exists(self, email_service):
        """Test that template directory exists and is accessible"""
        assert email_service.template_dir.exists()
        assert email_service.template_dir.is_dir()

    def test_cache_directory_creation(self, email_service):
        """Test that cache directory is created"""
        assert email_service.cache_dir.exists()
        assert email_service.cache_dir.is_dir()

    @pytest.mark.asyncio
    async def test_template_file_modification_detection(self, email_service, sample_template_data):
        """Test that template modification is detected for cache invalidation"""
        # This test would require file system manipulation
        # For now, just test that compilation works
        html = await email_service.compile_template("order_confirmation", sample_template_data)
        assert len(html) > 100

    @pytest.mark.asyncio
    async def test_concurrent_template_compilation(self, email_service, sample_template_data):
        """Test concurrent template compilation"""
        import asyncio
        
        # Compile multiple templates concurrently
        tasks = [
            email_service.compile_template("order_confirmation", sample_template_data),
            email_service.compile_template("order_shipped", sample_template_data),
            email_service.compile_template("order_delivered", sample_template_data)
        ]
        
        results = await asyncio.gather(*tasks)
        
        assert len(results) == 3
        for html in results:
            assert isinstance(html, str)
            assert len(html) > 100

    @pytest.mark.asyncio
    async def test_large_template_data_handling(self, email_service):
        """Test handling of large template data sets"""
        large_data = {
            "customer_name": "Test Customer",
            "order_id": "TEST-001",
            "order_items": [
                {
                    "product_name": f"Product {i}",
                    "quantity": i,
                    "unit_price": f"{i * 10}.99",
                    "total_price": f"{i * 10}.99"
                }
                for i in range(1, 51)  # 50 items
            ]
        }
        
        html = await email_service.compile_template("order_confirmation", large_data)
        
        assert isinstance(html, str)
        assert len(html) > 1000  # Should be substantial content
        assert "Product 50" in html  # Last item should be included