import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import get_current_user, get_rate_limiter
from app.models import Order, PaymentAttempt, User
from app.schemas import (
    PaymentIntentCreate,
    PaymentIntentResponse,
    PaymentStatus,
    PaymentWebhook,
)
from app.services.payment_service import PaymentService
from app.utils import (
    generate_correlation_id,
    generate_provider_ref,
    log_request,
    log_response,
)

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/intents", response_model=PaymentIntentResponse)
def create_payment_intent(
    payment_data: PaymentIntentCreate,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    rate_limit=Depends(get_rate_limiter()),
):
    """Create a payment intent (simulate payment provider)"""
    correlation_id = generate_correlation_id()
    start_time = time.time()

    log_request(request, correlation_id, current_user.id)

    try:
        # Verify order exists and belongs to user
        order = (
            db.query(Order)
            .filter(Order.id == payment_data.order_id, Order.user_id == current_user.id)
            .first()
        )

        if not order:
            log_response(correlation_id, 404, time.time() - start_time)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
            )

        if order.status != "pending":
            log_response(correlation_id, 400, time.time() - start_time)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Order is not in pending status",
            )

        # Create payment attempt
        payment_service = PaymentService(db)
        payment_attempt = payment_service.create_payment_intent(
            order_id=payment_data.order_id,
            amount=payment_data.amount,
            provider_ref=generate_provider_ref(),
        )

        # Simulate payment authorization (in real app, this would call payment provider)
        payment_attempt.status = PaymentStatus.AUTHORIZED
        order.status = "authorized"
        db.commit()

        log_response(correlation_id, 201, time.time() - start_time)
        return PaymentIntentResponse.model_validate(payment_attempt)

    except HTTPException:
        raise
    except Exception as e:
        log_response(correlation_id, 500, time.time() - start_time)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/webhook")
def payment_webhook(
    webhook_data: PaymentWebhook, request: Request, db: Session = Depends(get_db)
):
    """Handle payment webhook (simulate payment provider webhook)"""
    correlation_id = generate_correlation_id()
    start_time = time.time()

    log_request(request, correlation_id)

    try:
        # Find payment attempt by provider reference
        payment_attempt = (
            db.query(PaymentAttempt)
            .filter(PaymentAttempt.provider_ref == webhook_data.provider_ref)
            .first()
        )

        if not payment_attempt:
            log_response(correlation_id, 404, time.time() - start_time)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Payment attempt not found",
            )

        # Update payment status
        payment_attempt.status = webhook_data.status

        # Update order status based on payment status
        order = payment_attempt.order
        if webhook_data.status == PaymentStatus.CAPTURED:
            order.status = "captured"
        elif webhook_data.status == PaymentStatus.FAILED:
            order.status = "failed"

        db.commit()

        log_response(correlation_id, 200, time.time() - start_time)
        return {"status": "webhook_processed", "payment_id": payment_attempt.id}

    except HTTPException:
        raise
    except Exception as e:
        log_response(correlation_id, 500, time.time() - start_time)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
