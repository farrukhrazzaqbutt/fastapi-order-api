import logging
import time

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

from app.config import settings
from app.routers import auth, health, orders, payments
from app.utils import generate_correlation_id, log_request, log_response

# Configure logging
logging.basicConfig(level=getattr(logging, settings.log_level))
logger = logging.getLogger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"]
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

ORDERS_CREATED = Counter("orders_created_total", "Total orders created")

RATE_LIMITED_REQUESTS = Counter(
    "rate_limited_requests_total", "Total rate limited requests"
)

# Create FastAPI app
app = FastAPI(
    title="Order API",
    description=(
        "A production-ready FastAPI Order API with JWT auth, "
        "idempotency, rate limiting, and payments"
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=(
        ["*"] if settings.environment == "development" else ["https://yourdomain.com"]
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=(
        ["*"] if settings.environment == "development" else ["yourdomain.com"]
    ),
)


# Request logging middleware
@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    correlation_id = generate_correlation_id()
    start_time = time.time()

    # Add correlation ID to request state
    request.state.correlation_id = correlation_id

    # Log request
    log_request(request, correlation_id)

    # Process request
    response = await call_next(request)

    # Calculate duration
    duration = time.time() - start_time

    # Log response
    log_response(correlation_id, response.status_code, duration)

    # Update Prometheus metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code,
    ).inc()

    REQUEST_DURATION.labels(method=request.method, endpoint=request.url.path).observe(
        duration
    )

    # Add correlation ID to response headers
    response.headers["X-Correlation-ID"] = correlation_id

    return response


# Exception handlers
@app.exception_handler(429)
async def rate_limit_handler(request: Request, exc):
    RATE_LIMITED_REQUESTS.inc()
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"},
        headers={"Retry-After": "60"},
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    logger.error(f"Internal server error: {str(exc)}")
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


# Include routers
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(orders.router)
app.include_router(payments.router)


# Prometheus metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Order API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
    }


# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Order API starting up...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Database URL: {settings.database_url}")
    logger.info(f"Redis URL: {settings.redis_url}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Order API shutting down...")
