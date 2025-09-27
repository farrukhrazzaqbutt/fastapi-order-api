from typing import Optional

from sqlalchemy.orm import Session

from app.models import PaymentAttempt


class PaymentService:
    def __init__(self, db: Session):
        self.db = db

    def create_payment_intent(
        self, order_id: int, amount: float, provider_ref: str
    ) -> PaymentAttempt:
        """Create a payment intent"""
        payment_attempt = PaymentAttempt(
            order_id=order_id,
            provider_ref=provider_ref,
            amount=amount,
            status="pending",
        )

        self.db.add(payment_attempt)
        self.db.commit()
        self.db.refresh(payment_attempt)

        return payment_attempt

    def get_payment_by_provider_ref(
        self, provider_ref: str
    ) -> Optional[PaymentAttempt]:
        """Get payment attempt by provider reference"""
        return (
            self.db.query(PaymentAttempt)
            .filter(PaymentAttempt.provider_ref == provider_ref)
            .first()
        )

    def update_payment_status(
        self, payment_id: int, status: str
    ) -> Optional[PaymentAttempt]:
        """Update payment status"""
        payment = (
            self.db.query(PaymentAttempt)
            .filter(PaymentAttempt.id == payment_id)
            .first()
        )
        if payment:
            payment.status = status
            self.db.commit()
            self.db.refresh(payment)
        return payment
