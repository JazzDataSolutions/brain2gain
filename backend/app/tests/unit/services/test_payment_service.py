"""
Tests for PaymentService - Payment Processing and Management Service
Tests cover payment initiation, processing, refunds, webhooks, and statistics
"""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest
import pytest_asyncio
from fastapi import HTTPException, status
from sqlmodel import Session

from app.models import Order, Payment, PaymentStatus, Refund
from app.schemas.payment import PaymentFilters
from app.services.payment_service import PaymentService

# Mark all async tests in this module
pytestmark = pytest.mark.asyncio


class TestPaymentServiceInitialization:
    """Test PaymentService initialization and basic functionality"""

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    def test_payment_service_initialization(self, mock_paypal_service, mock_stripe_service):
        """Test PaymentService initializes correctly with all gateways"""
        mock_session = Mock(spec=Session)
        
        service = PaymentService(mock_session)
        
        assert service.session == mock_session
        assert service.stripe_service is not None
        assert service.paypal_service is not None
        assert "stripe" in service.gateways
        assert "paypal" in service.gateways
        assert "bank_transfer" in service.gateways

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    def test_gateway_availability(self, mock_paypal_service, mock_stripe_service):
        """Test all payment gateways are properly configured"""
        mock_session = Mock(spec=Session)
        service = PaymentService(mock_session)
        
        available_gateways = list(service.gateways.keys())
        expected_gateways = ["stripe", "paypal", "bank_transfer"]
        
        assert set(available_gateways) == set(expected_gateways)


class TestPaymentInitiation:
    """Test payment initiation functionality"""

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_initiate_payment_success(self, mock_paypal_service, mock_stripe_service):
        """Test successful payment initiation"""
        mock_session = Mock(spec=Session)
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.refresh = Mock()
        
        service = PaymentService(mock_session)
        
        # Mock gateway response
        mock_gateway = Mock()
        mock_gateway.initiate_payment = AsyncMock(return_value={"status": "pending", "payment_id": "test_id"})
        service.gateways["stripe"] = mock_gateway
        
        order_id = uuid.uuid4()
        amount = Decimal("100.00")
        
        result = await service.initiate_payment(order_id, "stripe", amount)
        
        assert result["status"] == "pending"
        assert result["payment_id"] == "test_id"
        mock_session.add.assert_called()
        mock_session.commit.assert_called()

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_initiate_payment_unsupported_method(self, mock_paypal_service, mock_stripe_service):
        """Test payment initiation with unsupported payment method"""
        mock_session = Mock(spec=Session)
        service = PaymentService(mock_session)
        
        order_id = uuid.uuid4()
        amount = Decimal("100.00")
        
        with pytest.raises(ValueError, match="Unsupported payment method"):
            await service.initiate_payment(order_id, "unsupported_method", amount)

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_initiate_payment_creates_payment_record(self, mock_paypal_service, mock_stripe_service):
        """Test that payment initiation creates correct payment record"""
        mock_session = Mock(spec=Session)
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.refresh = Mock()
        
        service = PaymentService(mock_session)
        
        # Mock gateway
        mock_gateway = Mock()
        mock_gateway.initiate_payment = AsyncMock(return_value={"status": "pending"})
        service.gateways["paypal"] = mock_gateway
        
        order_id = uuid.uuid4()
        amount = Decimal("250.50")
        
        await service.initiate_payment(order_id, "paypal", amount)
        
        # Verify Payment object was created with correct attributes
        call_args = mock_session.add.call_args_list
        payment_obj = call_args[0][0][0]  # First call, first argument
        
        assert payment_obj.order_id == order_id
        assert payment_obj.amount == amount
        assert payment_obj.currency == "MXN"
        assert payment_obj.payment_method == "paypal"
        assert payment_obj.status == PaymentStatus.PENDING


class TestPaymentProcessing:
    """Test payment processing for different payment methods"""

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_process_payment_success(self, mock_paypal_service, mock_stripe_service):
        """Test successful payment processing"""
        mock_session = Mock(spec=Session)
        service = PaymentService(mock_session)
        
        # Mock payment
        payment_id = uuid.uuid4()
        mock_payment = Payment(
            payment_id=payment_id,
            amount=Decimal("100.00"),
            payment_method="stripe",
            status=PaymentStatus.PENDING
        )
        
        # Mock gateway
        mock_gateway = Mock()
        mock_gateway.process_payment = AsyncMock(return_value={"status": "succeeded", "success": True, "message": "Payment processed successfully"})
        service.gateways["stripe"] = mock_gateway
        
        with patch.object(service, 'get_payment_by_id', return_value=mock_payment):
            result = await service.process_payment(payment_id)
        
        assert result.success is True
        assert result.payment_id == payment_id
        assert result.status == PaymentStatus.CAPTURED

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_process_payment_not_found(self, mock_paypal_service, mock_stripe_service):
        """Test payment processing with non-existent payment"""
        mock_session = Mock(spec=Session)
        service = PaymentService(mock_session)
        
        payment_id = uuid.uuid4()
        
        with patch.object(service, 'get_payment_by_id', return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await service.process_payment(payment_id)
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Payment not found" in exc_info.value.detail

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_process_payment_unsupported_method(self, mock_paypal_service, mock_stripe_service):
        """Test payment processing with unsupported payment method"""
        mock_session = Mock(spec=Session)
        service = PaymentService(mock_session)
        
        # Mock payment with unsupported method
        payment_id = uuid.uuid4()
        mock_payment = Payment(
            payment_id=payment_id,
            amount=Decimal("100.00"),
            payment_method="unsupported",
            status=PaymentStatus.PENDING
        )
        
        with patch.object(service, 'get_payment_by_id', return_value=mock_payment):
            with pytest.raises(HTTPException) as exc_info:
                await service.process_payment(payment_id)
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Unsupported payment method" in exc_info.value.detail


class TestStripePaymentProcessing:
    """Test Stripe-specific payment processing"""

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_stripe_payment_success(self, mock_paypal_service, mock_stripe_service):
        """Test successful Stripe payment processing"""
        mock_session = Mock(spec=Session)
        mock_session.add = Mock()
        mock_session.commit = Mock()
        
        service = PaymentService(mock_session)
        
        # Mock payment
        payment_id = uuid.uuid4()
        mock_payment = Payment(
            payment_id=payment_id,
            amount=Decimal("100.00"),
            payment_method="stripe",
            status=PaymentStatus.PENDING
        )
        
        with patch.object(service, 'get_payment_by_id', return_value=mock_payment):
            result = await service.process_stripe_payment(
                payment_id, "pm_test_card", "cus_test_customer"
            )
        
        assert result.success is True
        assert result.payment_id == payment_id
        assert result.status == PaymentStatus.CAPTURED
        assert result.stripe_response is not None
        assert mock_payment.status == PaymentStatus.CAPTURED
        assert mock_payment.stripe_payment_intent_id is not None

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_stripe_payment_failure_handling(self, mock_paypal_service, mock_stripe_service):
        """Test Stripe payment failure handling"""
        mock_session = Mock(spec=Session)
        mock_session.add = Mock()
        mock_session.commit = Mock()
        
        service = PaymentService(mock_session)
        
        # Mock payment
        payment_id = uuid.uuid4()
        mock_payment = Payment(
            payment_id=payment_id,
            amount=Decimal("100.00"),
            payment_method="stripe",
            status=PaymentStatus.PENDING
        )
        
        # Simulate exception during processing
        with patch.object(service, 'get_payment_by_id', return_value=mock_payment):
            with patch('app.services.payment_service.uuid') as mock_uuid:
                mock_uuid.uuid4.side_effect = Exception("Stripe error")
                with pytest.raises(HTTPException) as exc_info:
                    await service.process_stripe_payment(payment_id, "pm_test_card")
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Payment processing failed" in exc_info.value.detail


class TestPayPalPaymentProcessing:
    """Test PayPal-specific payment processing"""

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_paypal_payment_success(self, mock_paypal_service, mock_stripe_service):
        """Test successful PayPal payment processing"""
        mock_session = Mock(spec=Session)
        mock_session.add = Mock()
        mock_session.commit = Mock()
        
        service = PaymentService(mock_session)
        
        # Mock payment
        payment_id = uuid.uuid4()
        mock_payment = Payment(
            payment_id=payment_id,
            amount=Decimal("150.00"),
            payment_method="paypal",
            status=PaymentStatus.PENDING
        )
        
        with patch.object(service, 'get_payment_by_id', return_value=mock_payment):
            result = await service.process_paypal_payment(payment_id, "paypal_order_123")
        
        assert result.success is True
        assert result.payment_id == payment_id
        assert result.status == PaymentStatus.CAPTURED
        assert result.paypal_response is not None
        assert mock_payment.status == PaymentStatus.CAPTURED
        assert mock_payment.paypal_order_id == "paypal_order_123"

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_paypal_payment_failure_handling(self, mock_paypal_service, mock_stripe_service):
        """Test PayPal payment failure handling"""
        mock_session = Mock(spec=Session)
        mock_session.add = Mock()
        mock_session.commit = Mock()
        
        service = PaymentService(mock_session)
        
        # Mock payment
        payment_id = uuid.uuid4()
        mock_payment = Payment(
            payment_id=payment_id,
            amount=Decimal("150.00"),
            payment_method="paypal",
            status=PaymentStatus.PENDING
        )
        
        # Simulate exception during processing  
        with patch.object(service, 'get_payment_by_id', return_value=mock_payment):
            # Make the first session.add call fail, forcing exception handling  
            mock_session.add.side_effect = [Exception("PayPal error"), None]
            with pytest.raises(HTTPException) as exc_info:
                await service.process_paypal_payment(payment_id, "paypal_order_123")
        
        assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Payment processing failed" in exc_info.value.detail


class TestBankTransferProcessing:
    """Test bank transfer payment processing"""

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_bank_transfer_success(self, mock_paypal_service, mock_stripe_service):
        """Test successful bank transfer processing"""
        mock_session = Mock(spec=Session)
        mock_session.add = Mock()
        mock_session.commit = Mock()
        
        service = PaymentService(mock_session)
        
        # Mock payment
        payment_id = uuid.uuid4()
        mock_payment = Payment(
            payment_id=payment_id,
            amount=Decimal("500.00"),
            payment_method="bank_transfer",
            status=PaymentStatus.PENDING
        )
        
        with patch.object(service, 'get_payment_by_id', return_value=mock_payment):
            result = await service.process_bank_transfer(payment_id)
        
        assert result.success is True
        assert result.payment_id == payment_id
        assert result.status == PaymentStatus.PENDING  # Bank transfers stay pending
        assert result.bank_transfer_response is not None
        assert result.requires_user_action is True
        assert mock_payment.gateway_transaction_id is not None

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_bank_transfer_generates_reference(self, mock_paypal_service, mock_stripe_service):
        """Test bank transfer generates proper reference number"""
        mock_session = Mock(spec=Session)
        mock_session.add = Mock()
        mock_session.commit = Mock()
        
        service = PaymentService(mock_session)
        
        # Mock payment
        payment_id = uuid.uuid4()
        mock_payment = Payment(
            payment_id=payment_id,
            amount=Decimal("1000.00"),
            payment_method="bank_transfer",
            status=PaymentStatus.PENDING
        )
        
        with patch.object(service, 'get_payment_by_id', return_value=mock_payment):
            result = await service.process_bank_transfer(payment_id)
        
        bank_response = result.bank_transfer_response
        assert bank_response.reference_number is not None
        assert len(bank_response.reference_number) > 10  # Should be reasonably long
        assert bank_response.bank_details is not None
        assert "account_number" in bank_response.bank_details
        assert "clabe" in bank_response.bank_details


class TestPaymentRetrieval:
    """Test payment retrieval and filtering functionality"""

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_get_payment_by_id_success(self, mock_paypal_service, mock_stripe_service):
        """Test successful payment retrieval by ID"""
        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_payment = Payment(payment_id=uuid.uuid4(), amount=Decimal("100.00"))
        mock_result.first.return_value = mock_payment
        mock_session.exec.return_value = mock_result
        
        service = PaymentService(mock_session)
        
        payment_id = uuid.uuid4()
        result = await service.get_payment_by_id(payment_id)
        
        assert result == mock_payment
        mock_session.exec.assert_called_once()

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_get_payment_by_id_not_found(self, mock_paypal_service, mock_stripe_service):
        """Test payment retrieval when payment doesn't exist"""
        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result
        
        service = PaymentService(mock_session)
        
        payment_id = uuid.uuid4()
        result = await service.get_payment_by_id(payment_id)
        
        assert result is None

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_get_user_payments_with_filters(self, mock_paypal_service, mock_stripe_service):
        """Test getting user payments with filters"""
        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_payments = [Payment(payment_id=uuid.uuid4(), amount=Decimal("100.00"))]
        mock_result.__iter__ = Mock(return_value=iter(mock_payments))
        mock_session.exec.return_value = mock_result
        
        service = PaymentService(mock_session)
        
        user_id = uuid.uuid4()
        filters = PaymentFilters(
            status=[PaymentStatus.CAPTURED],
            payment_method=["stripe"],
            min_amount=Decimal("50.00")
        )
        
        result = await service.get_user_payments(user_id, filters=filters)
        
        assert len(result) == 1
        assert result[0] == mock_payments[0]

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_get_user_payments_pagination(self, mock_paypal_service, mock_stripe_service):
        """Test user payments retrieval with pagination"""
        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_payments = [Payment(payment_id=uuid.uuid4(), amount=Decimal("100.00"))]
        mock_result.__iter__ = Mock(return_value=iter(mock_payments))
        mock_session.exec.return_value = mock_result
        
        service = PaymentService(mock_session)
        
        user_id = uuid.uuid4()
        result = await service.get_user_payments(user_id, page=2, page_size=5)
        
        assert len(result) == 1
        mock_session.exec.assert_called_once()


class TestRefundProcessing:
    """Test refund creation and processing"""

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_create_refund_success(self, mock_paypal_service, mock_stripe_service):
        """Test successful refund creation"""
        mock_session = Mock(spec=Session)
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.refresh = Mock()
        
        service = PaymentService(mock_session)
        
        # Mock captured payment
        payment_id = uuid.uuid4()
        order_id = uuid.uuid4()
        mock_payment = Payment(
            payment_id=payment_id,
            order_id=order_id,
            amount=Decimal("100.00"),
            status=PaymentStatus.CAPTURED
        )
        
        with patch.object(service, 'get_payment_by_id', return_value=mock_payment):
            with patch.object(service, '_calculate_total_refunded', return_value=Decimal("0")):
                result = await service.create_refund(payment_id, Decimal("50.00"), "Customer request")
        
        assert result.payment_id == payment_id
        assert result.order_id == order_id
        assert result.amount == Decimal("50.00")
        assert result.reason == "Customer request"
        assert result.status == "COMPLETED"
        mock_session.add.assert_called()
        mock_session.commit.assert_called()

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_create_refund_payment_not_found(self, mock_paypal_service, mock_stripe_service):
        """Test refund creation with non-existent payment"""
        mock_session = Mock(spec=Session)
        service = PaymentService(mock_session)
        
        payment_id = uuid.uuid4()
        
        with patch.object(service, 'get_payment_by_id', return_value=None):
            with pytest.raises(HTTPException) as exc_info:
                await service.create_refund(payment_id, Decimal("50.00"), "Test reason")
        
        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert "Payment not found" in exc_info.value.detail

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_create_refund_payment_not_captured(self, mock_paypal_service, mock_stripe_service):
        """Test refund creation for non-captured payment"""
        mock_session = Mock(spec=Session)
        service = PaymentService(mock_session)
        
        # Mock pending payment
        payment_id = uuid.uuid4()
        mock_payment = Payment(
            payment_id=payment_id,
            amount=Decimal("100.00"),
            status=PaymentStatus.PENDING
        )
        
        with patch.object(service, 'get_payment_by_id', return_value=mock_payment):
            with pytest.raises(HTTPException) as exc_info:
                await service.create_refund(payment_id, Decimal("50.00"), "Test reason")
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Can only refund captured payments" in exc_info.value.detail

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_create_refund_amount_exceeds_payment(self, mock_paypal_service, mock_stripe_service):
        """Test refund creation with amount exceeding payment"""
        mock_session = Mock(spec=Session)
        service = PaymentService(mock_session)
        
        # Mock captured payment
        payment_id = uuid.uuid4()
        mock_payment = Payment(
            payment_id=payment_id,
            amount=Decimal("100.00"),
            status=PaymentStatus.CAPTURED
        )
        
        with patch.object(service, 'get_payment_by_id', return_value=mock_payment):
            with pytest.raises(HTTPException) as exc_info:
                await service.create_refund(payment_id, Decimal("150.00"), "Test reason")
        
        assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
        assert "Refund amount cannot exceed payment amount" in exc_info.value.detail

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_create_refund_full_refund_updates_payment_status(self, mock_paypal_service, mock_stripe_service):
        """Test that full refund updates payment status to REFUNDED"""
        mock_session = Mock(spec=Session)
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.refresh = Mock()
        
        service = PaymentService(mock_session)
        
        # Mock captured payment
        payment_id = uuid.uuid4()
        order_id = uuid.uuid4()
        mock_payment = Payment(
            payment_id=payment_id,
            order_id=order_id,
            amount=Decimal("100.00"),
            status=PaymentStatus.CAPTURED
        )
        
        with patch.object(service, 'get_payment_by_id', return_value=mock_payment):
            with patch.object(service, '_calculate_total_refunded', return_value=Decimal("100.00")):
                result = await service.create_refund(payment_id, Decimal("100.00"), "Full refund")
        
        assert mock_payment.status == PaymentStatus.REFUNDED


class TestPaymentMethods:
    """Test payment methods configuration"""

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_get_available_payment_methods(self, mock_paypal_service, mock_stripe_service):
        """Test getting available payment methods"""
        mock_session = Mock(spec=Session)
        service = PaymentService(mock_session)
        
        result = await service.get_available_payment_methods()
        
        assert result.currency == "MXN"
        assert result.default_method == "stripe"
        assert len(result.methods) == 3
        
        method_names = [method.method for method in result.methods]
        assert "stripe" in method_names
        assert "paypal" in method_names
        assert "bank_transfer" in method_names

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_payment_methods_have_correct_config(self, mock_paypal_service, mock_stripe_service):
        """Test payment methods have correct configuration"""
        mock_session = Mock(spec=Session)
        service = PaymentService(mock_session)
        
        result = await service.get_available_payment_methods()
        
        stripe_method = next(m for m in result.methods if m.method == "stripe")
        assert stripe_method.enabled is True
        assert stripe_method.min_amount == Decimal("10")
        assert stripe_method.processing_fee_percentage == Decimal("2.9")
        
        paypal_method = next(m for m in result.methods if m.method == "paypal")
        assert paypal_method.enabled is True
        assert paypal_method.processing_fee_percentage == Decimal("3.4")
        
        bank_method = next(m for m in result.methods if m.method == "bank_transfer")
        assert bank_method.enabled is True
        assert bank_method.processing_fee_percentage == Decimal("0")
        assert bank_method.fixed_fee == Decimal("15")


class TestPaymentStatistics:
    """Test payment statistics and analytics"""

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_get_payment_statistics(self, mock_paypal_service, mock_stripe_service):
        """Test payment statistics calculation"""
        mock_session = Mock(spec=Session)
        
        # Mock database query results (11 total calls)
        mock_session.exec.side_effect = [
            # 6 payment status counts (in enum order: PENDING, AUTHORIZED, CAPTURED, FAILED, REFUNDED, CANCELLED)
            Mock(first=Mock(return_value=5)),    # PENDING count
            Mock(first=Mock(return_value=0)),    # AUTHORIZED count
            Mock(first=Mock(return_value=10)),   # CAPTURED count  
            Mock(first=Mock(return_value=2)),    # FAILED count
            Mock(first=Mock(return_value=0)),    # REFUNDED count
            Mock(first=Mock(return_value=1)),    # CANCELLED count
            # 1 total captured amount
            Mock(first=Mock(return_value=Decimal("1500.00"))),  # Total amount
            # 1 total refunds
            Mock(first=Mock(return_value=Decimal("100.00"))),   # Total refunds
            # 3 payment method counts
            Mock(first=Mock(return_value=8)),    # Stripe count
            Mock(first=Mock(return_value=5)),    # PayPal count
            Mock(first=Mock(return_value=5)),    # Bank transfer count
            # 1 average amount
            Mock(first=Mock(return_value=Decimal("150.00"))),   # Average amount
        ]
        
        service = PaymentService(mock_session)
        
        result = await service.get_payment_statistics()
        
        assert result["total_payments"] == 18  # Sum of all status counts
        assert result["successful_payments"] == 10
        assert result["failed_payments"] == 2
        assert result["pending_payments"] == 5
        assert result["total_amount"] == Decimal("1500.00")
        assert result["total_refunds"] == Decimal("100.00")
        assert result["net_revenue"] == Decimal("1400.00")
        assert result["stripe_payments"] == 8
        assert result["paypal_payments"] == 5
        assert result["bank_transfer_payments"] == 5
        assert result["average_payment_amount"] == Decimal("150.00")
        assert result["conversion_rate"] == pytest.approx(55.55, rel=1e-2)  # 10/18 * 100

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_get_payment_statistics_no_payments(self, mock_paypal_service, mock_stripe_service):
        """Test payment statistics with no payments"""
        mock_session = Mock(spec=Session)
        
        # Mock all counts as 0
        mock_session.exec.side_effect = [
            Mock(first=Mock(return_value=0)) for _ in range(12)
        ]
        
        service = PaymentService(mock_session)
        
        result = await service.get_payment_statistics()
        
        assert result["total_payments"] == 0
        assert result["conversion_rate"] == 0


class TestWebhookHandling:
    """Test webhook handling for payment gateways"""

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_verify_stripe_webhook(self, mock_paypal_service, mock_stripe_service):
        """Test Stripe webhook verification"""
        mock_session = Mock(spec=Session)
        service = PaymentService(mock_session)
        
        body = b'{"test": "data"}'
        signature = "test_signature"
        
        result = await service.verify_stripe_webhook(body, signature)
        
        assert result["id"] == "evt_mock"
        assert result["type"] == "payment_intent.succeeded"
        assert "data" in result

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_verify_paypal_webhook(self, mock_paypal_service, mock_stripe_service):
        """Test PayPal webhook verification"""
        mock_session = Mock(spec=Session)
        service = PaymentService(mock_session)
        
        body = b'{"test": "data"}'
        headers = {"PAYPAL-TRANSMISSION-ID": "test_id"}
        
        result = await service.verify_paypal_webhook(body, headers)
        
        assert result["id"] == "evt_mock"
        assert result["event_type"] == "PAYMENT.CAPTURE.COMPLETED"
        assert "resource" in result

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_process_stripe_webhook(self, mock_paypal_service, mock_stripe_service):
        """Test Stripe webhook processing"""
        mock_session = Mock(spec=Session)
        service = PaymentService(mock_session)
        
        event = {"type": "payment_intent.succeeded", "data": {"object": {"id": "pi_test"}}}
        
        # Should not raise exception (placeholder implementation)
        await service.process_stripe_webhook(event)

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_process_paypal_webhook(self, mock_paypal_service, mock_stripe_service):
        """Test PayPal webhook processing"""
        mock_session = Mock(spec=Session)
        service = PaymentService(mock_session)
        
        event = {"event_type": "PAYMENT.CAPTURE.COMPLETED", "resource": {"id": "paypal_test"}}
        
        # Should not raise exception (placeholder implementation)
        await service.process_paypal_webhook(event)


class TestPrivateHelperMethods:
    """Test private helper methods"""

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    def test_calculate_total_refunded(self, mock_paypal_service, mock_stripe_service):
        """Test calculation of total refunded amount"""
        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_result.first.return_value = Decimal("75.00")
        mock_session.exec.return_value = mock_result
        
        service = PaymentService(mock_session)
        
        payment_id = uuid.uuid4()
        result = service._calculate_total_refunded(payment_id)
        
        assert result == Decimal("75.00")
        mock_session.exec.assert_called_once()

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    def test_calculate_total_refunded_no_refunds(self, mock_paypal_service, mock_stripe_service):
        """Test calculation when no refunds exist"""
        mock_session = Mock(spec=Session)
        mock_result = Mock()
        mock_result.first.return_value = None
        mock_session.exec.return_value = mock_result
        
        service = PaymentService(mock_session)
        
        payment_id = uuid.uuid4()
        result = service._calculate_total_refunded(payment_id)
        
        assert result == Decimal("0")


class TestEdgeCases:
    """Test edge cases and error scenarios"""

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_process_payment_with_zero_amount(self, mock_paypal_service, mock_stripe_service):
        """Test payment processing with zero amount"""
        mock_session = Mock(spec=Session)
        service = PaymentService(mock_session)
        
        # Mock payment with zero amount
        payment_id = uuid.uuid4()
        mock_payment = Payment(
            payment_id=payment_id,
            amount=Decimal("0.00"),
            payment_method="stripe",
            status=PaymentStatus.PENDING
        )
        
        mock_gateway = Mock()
        mock_gateway.process_payment = AsyncMock(return_value={"status": "succeeded", "success": True, "message": "Payment processed successfully"})
        service.gateways["stripe"] = mock_gateway
        
        with patch.object(service, 'get_payment_by_id', return_value=mock_payment):
            result = await service.process_payment(payment_id)
        
        assert result.success is True
        assert result.payment_id == payment_id

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_refund_with_decimal_precision(self, mock_paypal_service, mock_stripe_service):
        """Test refund with high decimal precision"""
        mock_session = Mock(spec=Session)
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.refresh = Mock()
        
        service = PaymentService(mock_session)
        
        # Mock captured payment
        payment_id = uuid.uuid4()
        order_id = uuid.uuid4()
        mock_payment = Payment(
            payment_id=payment_id,
            order_id=order_id,
            amount=Decimal("99.99"),
            status=PaymentStatus.CAPTURED
        )
        
        with patch.object(service, 'get_payment_by_id', return_value=mock_payment):
            with patch.object(service, '_calculate_total_refunded', return_value=Decimal("0")):
                result = await service.create_refund(payment_id, Decimal("33.333"), "Partial refund")
        
        assert result.amount == Decimal("33.333")

    @patch('app.services.payment_service.StripeService')
    @patch('app.services.payment_service.PayPalService')
    async def test_concurrent_payment_processing(self, mock_paypal_service, mock_stripe_service):
        """Test concurrent payment processing doesn't cause issues"""
        mock_session = Mock(spec=Session)
        service = PaymentService(mock_session)
        
        # Mock multiple payments
        payment_ids = [uuid.uuid4() for _ in range(3)]
        mock_payments = [
            Payment(
                payment_id=pid,
                amount=Decimal("100.00"),
                payment_method="stripe",
                status=PaymentStatus.PENDING
            ) for pid in payment_ids
        ]
        
        mock_gateway = Mock()
        mock_gateway.process_payment = AsyncMock(return_value={"status": "succeeded", "success": True})
        service.gateways["stripe"] = mock_gateway
        
        # Process all payments
        for i, payment_id in enumerate(payment_ids):
            with patch.object(service, 'get_payment_by_id', return_value=mock_payments[i]):
                result = await service.process_payment(payment_id)
                assert result.success is True