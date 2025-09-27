import logging
import uuid
from typing import Optional

from fastapi import Request

from app.deps import get_client_ip

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracing"""
    return str(uuid.uuid4())


def log_request(request: Request, correlation_id: str, user_id: Optional[int] = None):
    """Log request with correlation ID"""
    client_ip = get_client_ip(request)
    logger.info(
        f"Request: {request.method} {request.url.path} - "
        f"IP: {client_ip} - "
        f"Correlation ID: {correlation_id} - "
        f"User ID: {user_id or 'anonymous'}"
    )


def log_response(correlation_id: str, status_code: int, response_time: float):
    """Log response with correlation ID"""
    logger.info(
        f"Response: {status_code} - "
        f"Correlation ID: {correlation_id} - "
        f"Response Time: {response_time:.3f}s"
    )


def generate_provider_ref() -> str:
    """Generate a mock payment provider reference"""
    return f"pay_{uuid.uuid4().hex[:16]}"


def calculate_total_price(price: float, quantity: int) -> float:
    """Calculate total price with basic validation"""
    if price <= 0 or quantity <= 0:
        raise ValueError("Price and quantity must be positive")
    return round(price * quantity, 2)
