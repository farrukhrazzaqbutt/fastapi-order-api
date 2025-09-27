import logging
import time

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.deps import (
    check_idempotency,
    get_current_user,
    get_idempotency_key,
    get_rate_limiter,
    store_idempotency,
)
from app.models import User
from app.schemas import OrderCreate, OrderListResponse, OrderResponse
from app.services.order_service import OrderService
from app.utils import (
    calculate_total_price,
    generate_correlation_id,
    log_request,
    log_response,
)
from app.workers.tasks import send_order_confirmation_email

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/", response_model=OrderResponse)
def create_order(
    order_data: OrderCreate,
    request: Request,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    rate_limit=Depends(get_rate_limiter()),
    idem_key: str = Depends(get_idempotency_key),
):
    """Create a new order with idempotency and rate limiting"""
    correlation_id = generate_correlation_id()
    start_time = time.time()

    log_request(request, correlation_id, current_user.id)

    # Check idempotency
    cached_result = check_idempotency(idem_key)
    if cached_result:
        log_response(correlation_id, 200, time.time() - start_time)
        return OrderResponse(**cached_result)

    try:
        # Validate order data
        calculate_total_price(order_data.price, order_data.quantity)

        # Create order using service
        order_service = OrderService(db)
        order = order_service.create_order(
            user_id=current_user.id,
            item=order_data.item,
            quantity=order_data.quantity,
            price=order_data.price,
            idem_key=idem_key,
        )

        # Store result for idempotency
        order_response = OrderResponse.model_validate(order)
        store_idempotency(idem_key, order_response.model_dump())

        # Add background task for email notification (skip in test environment)
        try:
            background_tasks.add_task(
                send_order_confirmation_email,
                order.id,
                current_user.username,
                order.item,
            )
        except Exception as e:
            # Log error but don't fail the request
            logger.warning(f"Failed to add background task: {e}")

        log_response(correlation_id, 201, time.time() - start_time)
        return order_response

    except ValueError as e:
        log_response(correlation_id, 400, time.time() - start_time)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception:
        log_response(correlation_id, 500, time.time() - start_time)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/", response_model=OrderListResponse)
def get_orders(
    request: Request,
    page: int = 1,
    size: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    rate_limit=Depends(get_rate_limiter()),
):
    """Get user's orders with pagination"""
    correlation_id = generate_correlation_id()
    start_time = time.time()

    log_request(request, correlation_id, current_user.id)

    try:
        order_service = OrderService(db)
        orders, total = order_service.get_user_orders(
            user_id=current_user.id, page=page, size=size
        )

        order_responses = [OrderResponse.model_validate(order) for order in orders]

        log_response(correlation_id, 200, time.time() - start_time)
        return OrderListResponse(
            orders=order_responses, total=total, page=page, size=size
        )

    except Exception:
        log_response(correlation_id, 500, time.time() - start_time)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    rate_limit=Depends(get_rate_limiter()),
):
    """Get a specific order by ID"""
    correlation_id = generate_correlation_id()
    start_time = time.time()

    log_request(request, correlation_id, current_user.id)

    try:
        order_service = OrderService(db)
        order = order_service.get_order_by_id(order_id, current_user.id)

        if not order:
            log_response(correlation_id, 404, time.time() - start_time)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Order not found"
            )

        log_response(correlation_id, 200, time.time() - start_time)
        return OrderResponse.model_validate(order)

    except HTTPException:
        raise
    except Exception:
        log_response(correlation_id, 500, time.time() - start_time)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
