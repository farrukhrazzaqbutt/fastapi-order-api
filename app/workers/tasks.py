from celery import current_task
from app.workers.celery_app import celery_app
from app.db import SessionLocal
from app.models import Order
from app.services.order_service import OrderService
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True)
def send_order_confirmation_email(self, order_id: int, username: str, item: str):
    """Send order confirmation email (simulated)"""
    try:
        # Simulate email sending delay
        import time
        time.sleep(2)
        
        # In a real application, you would:
        # 1. Generate email content
        # 2. Send via email service (SendGrid, SES, etc.)
        # 3. Log the email status
        
        logger.info(f"Order confirmation email sent for order {order_id} to user {username} for item {item}")
        
        return {
            "status": "success",
            "order_id": order_id,
            "message": f"Confirmation email sent for order {order_id}"
        }
        
    except Exception as exc:
        logger.error(f"Failed to send email for order {order_id}: {str(exc)}")
        # Retry the task
        raise self.retry(exc=exc, countdown=60, max_retries=3)


@celery_app.task(bind=True)
def process_payment_webhook(self, provider_ref: str, status: str, amount: float):
    """Process payment webhook asynchronously"""
    try:
        db = SessionLocal()
        try:
            # Find payment attempt
            from app.models import PaymentAttempt
            payment = db.query(PaymentAttempt).filter(
                PaymentAttempt.provider_ref == provider_ref
            ).first()
            
            if not payment:
                logger.error(f"Payment attempt not found for provider_ref: {provider_ref}")
                return {"status": "error", "message": "Payment not found"}
            
            # Update payment and order status
            payment.status = status
            order = payment.order
            
            if status == "captured":
                order.status = "captured"
            elif status == "failed":
                order.status = "failed"
            
            db.commit()
            
            logger.info(f"Payment webhook processed: {provider_ref} -> {status}")
            
            return {
                "status": "success",
                "payment_id": payment.id,
                "order_id": order.id,
                "new_status": status
            }
            
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"Failed to process payment webhook {provider_ref}: {str(exc)}")
        raise self.retry(exc=exc, countdown=30, max_retries=3)


@celery_app.task
def cleanup_expired_orders():
    """Clean up expired orders (example background task)"""
    try:
        db = SessionLocal()
        try:
            from datetime import datetime, timedelta
            from sqlalchemy import and_
            
            # Find orders older than 24 hours that are still pending
            cutoff_time = datetime.utcnow() - timedelta(hours=24)
            
            expired_orders = db.query(Order).filter(
                and_(
                    Order.status == "pending",
                    Order.created_at < cutoff_time
                )
            ).all()
            
            for order in expired_orders:
                order.status = "cancelled"
                logger.info(f"Cancelled expired order: {order.id}")
            
            db.commit()
            
            logger.info(f"Cleaned up {len(expired_orders)} expired orders")
            
            return {"status": "success", "cancelled_orders": len(expired_orders)}
            
        finally:
            db.close()
            
    except Exception as exc:
        logger.error(f"Failed to cleanup expired orders: {str(exc)}")
        raise exc
