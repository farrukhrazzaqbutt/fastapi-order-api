from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    orders = relationship("Order", back_populates="user")


class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    item = Column(String(255), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    idem_key = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="orders")
    payment_attempts = relationship("PaymentAttempt", back_populates="order")
    
    # Indexes
    __table_args__ = (
        Index('idx_orders_user_id', 'user_id'),
        Index('idx_orders_status', 'status'),
        Index('idx_orders_created_at', 'created_at'),
    )


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    provider_ref = Column(String(255), nullable=False, index=True)
    amount = Column(Float, nullable=False)
    status = Column(String(50), default="pending", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    order = relationship("Order", back_populates="payment_attempts")
    
    # Indexes
    __table_args__ = (
        Index('idx_payment_attempts_order_id', 'order_id'),
        Index('idx_payment_attempts_status', 'status'),
        Index('idx_payment_attempts_created_at', 'created_at'),
    )
