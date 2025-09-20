from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class OrderStatus(str, Enum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    PENDING = "pending"
    AUTHORIZED = "authorized"
    CAPTURED = "captured"
    FAILED = "failed"


# User schemas
class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


# Order schemas
class OrderCreate(BaseModel):
    item: str = Field(..., min_length=1, max_length=255)
    quantity: int = Field(..., gt=0)
    price: float = Field(..., gt=0)


class OrderResponse(BaseModel):
    id: int
    user_id: int
    item: str
    quantity: int
    price: float
    status: OrderStatus
    idem_key: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class OrderListResponse(BaseModel):
    orders: List[OrderResponse]
    total: int
    page: int
    size: int


# Payment schemas
class PaymentIntentCreate(BaseModel):
    order_id: int
    amount: float = Field(..., gt=0)


class PaymentIntentResponse(BaseModel):
    id: int
    order_id: int
    provider_ref: str
    amount: float
    status: PaymentStatus
    created_at: datetime
    
    class Config:
        from_attributes = True


class PaymentWebhook(BaseModel):
    provider_ref: str
    status: PaymentStatus
    amount: float


# Health check
class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str = "1.0.0"
