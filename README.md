# Order API - Production-Ready FastAPI Application

A comprehensive, production-ready FastAPI application demonstrating modern web API development practices including JWT authentication, idempotency, rate limiting, background tasks, and payment processing.

## 🚀 Features

- **JWT Authentication** - Secure user authentication with access tokens
- **Idempotent Operations** - Safe retry mechanisms for order creation
- **Rate Limiting** - Redis-based rate limiting per IP address
- **Background Tasks** - Celery integration for async processing
- **Payment Processing** - Simulated payment intents and webhooks
- **Database Management** - SQLAlchemy 2.x with PostgreSQL
- **Comprehensive Testing** - Full test suite with pytest
- **Observability** - Prometheus metrics and structured logging
- **Docker Support** - Complete containerization with docker-compose
- **API Documentation** - Auto-generated Swagger/OpenAPI docs

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI App   │    │   PostgreSQL    │    │     Redis       │
│                 │    │                 │    │                 │
│ • JWT Auth      │◄──►│ • Users         │    │ • Rate Limiting │
│ • Rate Limiting │    │ • Orders        │    │ • Idempotency   │
│ • Idempotency   │    │ • Payments      │    │ • Celery Broker │
│ • Background    │    │                 │    │                 │
│   Tasks         │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐
│     Celery      │
│   Worker        │
│                 │
│ • Email Tasks   │
│ • Cleanup Jobs  │
│ • Webhooks      │
└─────────────────┘
```

## 🛠️ Tech Stack

- **Python 3.11** - Modern Python with latest features
- **FastAPI** - High-performance web framework
- **SQLAlchemy 2.x** - Modern ORM with async support
- **PostgreSQL 15** - Robust relational database
- **Redis 7** - In-memory data store for caching and queues
- **Celery** - Distributed task queue
- **Pytest** - Comprehensive testing framework
- **Docker & Docker Compose** - Containerization
- **Prometheus** - Metrics collection
- **Alembic** - Database migrations

## 📁 Project Structure

```
order-api/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration management
│   ├── db.py                # Database connection
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic schemas
│   ├── auth.py              # JWT authentication
│   ├── deps.py              # Dependencies and middleware
│   ├── utils.py             # Utility functions
│   ├── routers/             # API route handlers
│   │   ├── auth.py          # Authentication endpoints
│   │   ├── orders.py        # Order management
│   │   ├── payments.py      # Payment processing
│   │   └── health.py        # Health checks
│   ├── services/            # Business logic
│   │   ├── order_service.py
│   │   └── payment_service.py
│   └── workers/             # Background tasks
│       ├── celery_app.py
│       └── tasks.py
├── tests/                   # Test suite
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_orders.py
│   ├── test_payments.py
│   └── test_rate_limiting.py
├── alembic/                 # Database migrations
├── docker-compose.yml       # Multi-service setup
├── Dockerfile              # Container definition
├── requirements.txt        # Python dependencies
├── env.sample             # Environment variables template
└── README.md              # This file
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)

### 1. Clone and Setup

```bash
git clone <your-repo-url>
cd order-api
cp env.sample .env
```

### 2. Start Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api
```

### 3. Initialize Database

```bash
# Run migrations
docker-compose exec api alembic upgrade head

# Or run locally if you have Python installed
alembic upgrade head
```

### 4. Access the Application

- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Metrics**: http://localhost:8000/metrics
- **Health Check**: http://localhost:8000/health

## 📚 API Usage

### Authentication

```bash
# Seed admin user (development only)
curl -X POST http://localhost:8000/auth/seed

# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'

# Register new user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username": "newuser", "password": "password123"}'
```

### Order Management

```bash
# Create order (requires Idempotency-Key header)
curl -X POST http://localhost:8000/orders/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: unique-key-123" \
  -d '{
    "item": "Laptop",
    "quantity": 1,
    "price": 999.99
  }'

# Get orders
curl -X GET http://localhost:8000/orders/ \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get specific order
curl -X GET http://localhost:8000/orders/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Payment Processing

```bash
# Create payment intent
curl -X POST http://localhost:8000/payments/intents \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": 1,
    "amount": 999.99
  }'

# Simulate payment webhook
curl -X POST http://localhost:8000/payments/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "provider_ref": "pay_abc123",
    "status": "captured",
    "amount": 999.99
  }'
```

## 🧪 Testing

### Run Tests

```bash
# Run all tests
docker-compose exec api pytest

# Run with coverage
docker-compose exec api pytest --cov=app

# Run specific test file
docker-compose exec api pytest tests/test_orders.py -v
```

### Test Coverage

The test suite includes:

- **Authentication Tests** - Login, registration, JWT validation
- **Order Tests** - CRUD operations, idempotency, validation
- **Payment Tests** - Payment intents, webhooks, status updates
- **Rate Limiting Tests** - IP-based rate limiting verification
- **Integration Tests** - End-to-end workflow testing

## 📊 Monitoring & Observability

### Prometheus Metrics

- `http_requests_total` - Total HTTP requests by method, endpoint, status
- `http_request_duration_seconds` - Request duration histogram
- `orders_created_total` - Total orders created
- `rate_limited_requests_total` - Rate limited requests

### Logging

- Structured JSON logging with correlation IDs
- Request/response logging with timing
- Error tracking and debugging information

### Health Checks

- `/health` - Basic health check
- `/metrics` - Prometheus metrics endpoint

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://app:app@db:5432/app

# Redis
REDIS_URL=redis://redis:6379/0

# JWT
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO
```

## 🚀 Production Deployment

### Security Considerations

1. **Change default secrets** - Update JWT secret key
2. **Use environment-specific configs** - Different settings for dev/staging/prod
3. **Enable HTTPS** - Use reverse proxy (nginx) with SSL
4. **Database security** - Use connection pooling and encrypted connections
5. **Rate limiting** - Adjust limits based on expected traffic

### Scaling

- **Horizontal scaling** - Multiple API instances behind load balancer
- **Database scaling** - Read replicas for read-heavy workloads
- **Redis clustering** - For high availability
- **Celery scaling** - Multiple worker processes/nodes

### Monitoring

- **Application metrics** - Prometheus + Grafana
- **Log aggregation** - ELK stack or similar
- **Error tracking** - Sentry or similar
- **Uptime monitoring** - External monitoring services

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- FastAPI team for the excellent framework
- SQLAlchemy team for the powerful ORM
- All open-source contributors

---

**Note**: This is a demonstration project showcasing production-ready patterns. For production use, ensure proper security hardening, monitoring, and operational procedures are in place.
