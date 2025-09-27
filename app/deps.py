import json
from typing import Optional

import redis
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth import verify_token
from app.config import settings
from app.db import get_db
from app.models import User

security = HTTPBearer()

# Redis connection with fallback
try:
    redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    # Test connection
    redis_client.ping()
except Exception:
    # If Redis is not available, create a mock
    class MockRedis:
        def __init__(self):
            self.data = {}

        def get(self, key):
            return self.data.get(key)

        def set(self, key, value, ex=None):
            self.data[key] = value

        def setex(self, key, time, value):
            self.data[key] = value

        def incr(self, key, amount=1):
            current = int(self.data.get(key, 0))
            new_value = current + amount
            self.data[key] = str(new_value)
            return new_value

        def delete(self, key):
            self.data.pop(key, None)

        def flushdb(self):
            self.data.clear()

        def ping(self):
            return True

    redis_client = MockRedis()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """Get current authenticated user"""
    token = credentials.credentials
    payload = verify_token(token)
    username = payload.get("sub")

    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    # Check for forwarded headers first (for load balancers/proxies)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # Fallback to direct connection IP
    return request.client.host if request.client else "unknown"


def get_rate_limiter():
    """Rate limiting dependency using Redis token bucket"""

    def rate_limit(request: Request):
        client_ip = get_client_ip(request)
        key = f"rate_limit:{client_ip}"

        # Get current count and reset time
        current = redis_client.get(key)
        if current is None:
            # First request in window
            redis_client.setex(key, settings.rate_limit_window, 1)
            return True

        count = int(current)
        if count >= settings.rate_limit_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded",
            )

        # Increment counter
        redis_client.incr(key)
        return True

    return rate_limit


def get_idempotency_key(request: Request) -> str:
    """Extract idempotency key from request headers"""
    idem_key = request.headers.get("Idempotency-Key")
    if not idem_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Idempotency-Key header is required",
        )
    return idem_key


def check_idempotency(idem_key: str) -> Optional[dict]:
    """Check if request with this idempotency key was already processed"""
    cached_result = redis_client.get(f"idem:{idem_key}")
    if cached_result:
        return json.loads(cached_result)
    return None


def store_idempotency(idem_key: str, result: dict, ttl: int = 3600):
    """Store result for idempotency check"""
    redis_client.setex(f"idem:{idem_key}", ttl, json.dumps(result))
