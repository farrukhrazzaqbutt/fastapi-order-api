from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Order
from typing import List, Tuple, Optional


class OrderService:
    def __init__(self, db: Session):
        self.db = db

    def create_order(
        self, user_id: int, item: str, quantity: int, price: float, idem_key: str
    ) -> Order:
        """Create a new order"""
        order = Order(
            user_id=user_id,
            item=item,
            quantity=quantity,
            price=price,
            idem_key=idem_key,
            status="pending",
        )

        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)

        return order

    def get_user_orders(
        self, user_id: int, page: int = 1, size: int = 10
    ) -> Tuple[List[Order], int]:
        """Get user's orders with pagination"""
        # Calculate offset
        offset = (page - 1) * size

        # Get total count
        total = self.db.query(Order).filter(Order.user_id == user_id).count()

        # Get orders with pagination
        orders = (
            self.db.query(Order)
            .filter(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .offset(offset)
            .limit(size)
            .all()
        )

        return orders, total

    def get_order_by_id(self, order_id: int, user_id: int) -> Optional[Order]:
        """Get a specific order by ID for a user"""
        return (
            self.db.query(Order)
            .filter(Order.id == order_id, Order.user_id == user_id)
            .first()
        )

    def update_order_status(self, order_id: int, status: str) -> Optional[Order]:
        """Update order status"""
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if order:
            order.status = status
            self.db.commit()
            self.db.refresh(order)
        return order
