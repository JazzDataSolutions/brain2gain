"""
Tests for Email Delivery Service
Testing the production-ready email delivery infrastructure
"""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pydantic import EmailStr

from app.services.email_delivery_service import (
    EmailDeliveryResult,
    EmailDeliveryService,
    EmailPriority,
    EmailRequest,
    EmailStatus,
    DeliveryProvider,
)


class TestEmailDeliveryService:
    """Test suite for EmailDeliveryService"""

    @pytest.fixture
    def email_service(self):
        """Create EmailDeliveryService instance for testing"""
        with patch('app.services.email_delivery_service.EmailTemplateService'):
            service = EmailDeliveryService()
            return service

    @pytest.fixture
    def sample_email_request(self):
        """Sample email request for testing"""
        return EmailRequest(
            to="test@example.com",
            subject="Test Email",
            html_content="<h1>Test Email Content</h1>",
            priority=EmailPriority.NORMAL
        )

    @pytest.fixture
    def sample_order_data(self):
        """Sample order data for testing"""
        return {
            "order_id": "ORD-12345",
            "customer_name": "John Doe",
            "order_total": 150.99,
            "items": [
                {"name": "Whey Protein", "quantity": 2, "price": 75.50}
            ],
            "shipping_address": {
                "street": "123 Main St",
                "city": "Anytown",
                "state": "CA",
                "zip": "12345"
            },
            "order_date": "2025-06-30",
            "company_name": "Brain2Gain",
            "company_website": "https://brain2gain.com"
        }

    def test_get_delivery_provider_smtp_default(self, email_service):
        """Test that SMTP is used as default provider"""
        assert email_service.provider == DeliveryProvider.SMTP

    @pytest.mark.asyncio
    async def test_send_email_with_html_content(self, email_service, sample_email_request):
        """Test sending email with HTML content"""
        with patch.object(email_service, '_send_via_smtp') as mock_smtp:
            mock_smtp.return_value = EmailDeliveryResult(
                success=True,
                status=EmailStatus.SENT,
                message_id="test-message-id"
            )
            
            result = await email_service.send_email(sample_email_request)
            
            assert result.success is True
            assert result.status == EmailStatus.SENT
            mock_smtp.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_with_template(self, email_service):
        """Test sending email with MJML template"""
        email_request = EmailRequest(
            to="test@example.com",
            subject="Template Test",
            template_name="order_confirmation.mjml",
            template_data={"order_id": "123", "customer_name": "Test User"}
        )
        
        # Mock the template service
        with patch.object(email_service.template_service, 'compile_template') as mock_compile:
            mock_compile.return_value = asyncio.Future()
            mock_compile.return_value.set_result("<h1>Compiled Template</h1>")
            
            with patch.object(email_service, '_send_via_smtp') as mock_smtp:
                mock_smtp.return_value = EmailDeliveryResult(
                    success=True,
                    status=EmailStatus.SENT
                )
                
                result = await email_service.send_email(email_request)
                
                assert result.success is True
                mock_compile.assert_called_once()
                mock_smtp.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_missing_content(self, email_service):
        """Test error handling when neither template nor HTML content provided"""
        email_request = EmailRequest(
            to="test@example.com",
            subject="Test"
        )
        
        result = await email_service.send_email(email_request)
        
        assert result.success is False
        assert result.status == EmailStatus.FAILED
        assert "Either template_name with template_data or html_content must be provided" in result.error_message

    @pytest.mark.asyncio
    async def test_send_order_confirmation(self, email_service, sample_order_data):
        """Test sending order confirmation email"""
        with patch.object(email_service, 'send_email') as mock_send:
            mock_send.return_value = EmailDeliveryResult(
                success=True,
                status=EmailStatus.SENT
            )
            
            result = await email_service.send_order_confirmation(
                "customer@example.com",
                sample_order_data
            )
            
            assert result.success is True
            mock_send.assert_called_once()
            
            # Verify the email request parameters
            call_args = mock_send.call_args[0][0]
            assert call_args.to == "customer@example.com"
            assert "Confirmación de Pedido" in call_args.subject
            assert call_args.template_name == "order_confirmation.mjml"
            assert call_args.priority == EmailPriority.HIGH

    @pytest.mark.asyncio
    async def test_send_order_shipped(self, email_service, sample_order_data):
        """Test sending order shipped notification"""
        with patch.object(email_service, 'send_email') as mock_send:
            mock_send.return_value = EmailDeliveryResult(
                success=True,
                status=EmailStatus.SENT
            )
            
            result = await email_service.send_order_shipped(
                "customer@example.com",
                sample_order_data
            )
            
            assert result.success is True
            mock_send.assert_called_once()
            
            call_args = mock_send.call_args[0][0]
            assert "Ha Sido Enviado" in call_args.subject
            assert call_args.template_name == "order_shipped.mjml"

    @pytest.mark.asyncio
    async def test_send_order_delivered(self, email_service, sample_order_data):
        """Test sending order delivered notification"""
        with patch.object(email_service, 'send_email') as mock_send:
            mock_send.return_value = EmailDeliveryResult(
                success=True,
                status=EmailStatus.SENT
            )
            
            result = await email_service.send_order_delivered(
                "customer@example.com",
                sample_order_data
            )
            
            assert result.success is True
            mock_send.assert_called_once()
            
            call_args = mock_send.call_args[0][0]
            assert "Ha Sido Entregado" in call_args.subject
            assert call_args.template_name == "order_delivered.mjml"

    @pytest.mark.asyncio
    async def test_send_password_reset(self, email_service):
        """Test sending password reset email"""
        reset_data = {
            "user_name": "John Doe",
            "reset_token": "abc123",
            "expiry_hours": 48
        }
        
        with patch.object(email_service, 'send_email') as mock_send:
            mock_send.return_value = EmailDeliveryResult(
                success=True,
                status=EmailStatus.SENT
            )
            
            result = await email_service.send_password_reset(
                "user@example.com",
                reset_data
            )
            
            assert result.success is True
            mock_send.assert_called_once()
            
            call_args = mock_send.call_args[0][0]
            assert "Recuperación de Contraseña" in call_args.subject
            assert call_args.template_name == "reset_password.mjml"

    @pytest.mark.asyncio
    async def test_send_welcome_email(self, email_service):
        """Test sending welcome email"""
        user_data = {
            "user_name": "Jane Doe",
            "temporary_password": "temp123"
        }
        
        with patch.object(email_service, 'send_email') as mock_send:
            mock_send.return_value = EmailDeliveryResult(
                success=True,
                status=EmailStatus.SENT
            )
            
            result = await email_service.send_welcome_email(
                "newuser@example.com",
                user_data
            )
            
            assert result.success is True
            mock_send.assert_called_once()
            
            call_args = mock_send.call_args[0][0]
            assert "Bienvenido a Brain2Gain" in call_args.subject
            assert call_args.template_name == "new_account.mjml"

    @pytest.mark.asyncio
    async def test_send_bulk_emails(self, email_service):
        """Test sending bulk emails with rate limiting"""
        requests = [
            EmailRequest(
                to=f"user{i}@example.com",
                subject=f"Bulk Email {i}",
                html_content="<h1>Bulk Email Content</h1>"
            )
            for i in range(5)
        ]
        
        with patch.object(email_service, 'send_email') as mock_send:
            mock_send.return_value = EmailDeliveryResult(
                success=True,
                status=EmailStatus.SENT
            )
            
            results = await email_service.send_bulk_emails(
                requests,
                batch_size=2,
                delay_between_batches=0.1
            )
            
            assert len(results) == 5
            assert all(result.success for result in results)
            assert mock_send.call_count == 5

    @pytest.mark.asyncio
    async def test_send_bulk_emails_with_exceptions(self, email_service):
        """Test bulk email handling when some emails fail"""
        requests = [
            EmailRequest(
                to=f"user{i}@example.com",
                subject=f"Bulk Email {i}",
                html_content="<h1>Bulk Email Content</h1>"
            )
            for i in range(3)
        ]
        
        # Mock send_email to raise exception for second email
        async def mock_send_side_effect(request):
            if "user1" in str(request.to):
                raise Exception("SMTP connection failed")
            return EmailDeliveryResult(success=True, status=EmailStatus.SENT)
        
        with patch.object(email_service, 'send_email', side_effect=mock_send_side_effect):
            results = await email_service.send_bulk_emails(requests, batch_size=1)
            
            assert len(results) == 3
            assert results[0].success is True
            assert results[1].success is False
            assert "SMTP connection failed" in results[1].error_message
            assert results[2].success is True

    @pytest.mark.asyncio
    async def test_smtp_delivery_success(self, email_service, sample_email_request):
        """Test successful SMTP delivery"""
        with patch('app.services.email_delivery_service.aiosmtplib.SMTP') as mock_smtp_class:
            mock_smtp = AsyncMock()
            mock_smtp_class.return_value.__aenter__.return_value = mock_smtp
            
            result = await email_service._send_via_smtp(
                sample_email_request,
                "<h1>Test Content</h1>"
            )
            
            assert result.success is True
            assert result.status == EmailStatus.SENT
            mock_smtp.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_smtp_delivery_failure(self, email_service, sample_email_request):
        """Test SMTP delivery failure handling"""
        with patch('app.services.email_delivery_service.aiosmtplib.SMTP') as mock_smtp_class:
            mock_smtp_class.side_effect = Exception("SMTP connection failed")
            
            result = await email_service._send_via_smtp(
                sample_email_request,
                "<h1>Test Content</h1>"
            )
            
            assert result.success is False
            assert result.status == EmailStatus.FAILED
            assert "SMTP connection failed" in result.error_message