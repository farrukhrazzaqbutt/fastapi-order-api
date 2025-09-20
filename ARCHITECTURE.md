# Architecture Overview

## System Design

This Order API demonstrates a production-ready microservice architecture with the following key components:

### Core Components

1. **FastAPI Application** - High-performance web framework
2. **PostgreSQL Database** - Primary data store
3. **Redis** - Caching, rate limiting, and message broker
4. **Celery Workers** - Background task processing
5. **Prometheus** - Metrics collection and monitoring

### Data Flow

```
Client Request → FastAPI → Authentication → Rate Limiting → Business Logic → Database
                     ↓
              Background Tasks → Celery → Redis → Email/Notifications
                     ↓
              Metrics → Prometheus → Monitoring Dashboard
```

## Key Features Implementation

### 1. JWT Authentication
- **Implementation**: `app/auth.py`
- **Security**: Password hashing with bcrypt
- **Token Management**: Configurable expiration times
- **Dependency Injection**: `get_current_user()` in `app/deps.py`

### 2. Idempotency
- **Storage**: Redis with TTL
- **Key Generation**: Client-provided `Idempotency-Key` header
- **Scope**: Per-user, per-operation
- **Implementation**: `check_idempotency()` and `store_idempotency()` in `app/deps.py`

### 3. Rate Limiting
- **Algorithm**: Token bucket per IP address
- **Storage**: Redis with sliding window
- **Configuration**: Configurable requests per window
- **Implementation**: `get_rate_limiter()` in `app/deps.py`

### 4. Background Tasks
- **Queue**: Redis as Celery broker
- **Tasks**: Email notifications, cleanup jobs
- **Scaling**: Multiple worker processes
- **Implementation**: `app/workers/tasks.py`

### 5. Payment Processing
- **Intents**: Simulated payment provider integration
- **Webhooks**: Asynchronous payment status updates
- **State Management**: Order status transitions
- **Implementation**: `app/routers/payments.py`

## Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Orders Table
```sql
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    item VARCHAR(255) NOT NULL,
    quantity INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    idem_key VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### Payment Attempts Table
```sql
CREATE TABLE payment_attempts (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    provider_ref VARCHAR(255) NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## API Design Patterns

### RESTful Endpoints
- **Resource-based URLs**: `/orders`, `/payments`
- **HTTP Methods**: GET, POST, PUT, DELETE
- **Status Codes**: Proper HTTP status code usage
- **Content Negotiation**: JSON request/response

### Error Handling
- **Structured Errors**: Consistent error response format
- **HTTP Status Codes**: Appropriate status codes
- **Validation**: Pydantic model validation
- **Logging**: Structured logging with correlation IDs

### Security
- **Authentication**: JWT Bearer tokens
- **Authorization**: User-based resource access
- **Input Validation**: Pydantic schemas
- **Rate Limiting**: IP-based throttling
- **CORS**: Configurable cross-origin policies

## Monitoring & Observability

### Metrics (Prometheus)
- `http_requests_total` - Request count by method, endpoint, status
- `http_request_duration_seconds` - Request duration histogram
- `orders_created_total` - Order creation counter
- `rate_limited_requests_total` - Rate limiting counter

### Logging
- **Format**: Structured JSON logging
- **Correlation IDs**: Request tracing
- **Levels**: DEBUG, INFO, WARN, ERROR
- **Context**: User ID, IP address, timing

### Health Checks
- **Endpoint**: `/health`
- **Metrics**: `/metrics`
- **Dependencies**: Database and Redis connectivity

## Scalability Considerations

### Horizontal Scaling
- **Stateless Design**: No server-side session storage
- **Load Balancing**: Multiple API instances
- **Database**: Read replicas for read-heavy workloads
- **Cache**: Redis clustering for high availability

### Performance Optimization
- **Connection Pooling**: SQLAlchemy connection management
- **Caching**: Redis for frequently accessed data
- **Async Processing**: Background tasks for non-critical operations
- **Database Indexes**: Optimized queries

### Security Hardening
- **Secrets Management**: Environment variables
- **HTTPS**: SSL/TLS termination
- **Input Sanitization**: SQL injection prevention
- **Rate Limiting**: DDoS protection

## Deployment Architecture

### Container Strategy
- **Multi-stage Builds**: Optimized Docker images
- **Base Images**: Official Python 3.11 slim
- **Security**: Non-root user execution
- **Size Optimization**: Minimal dependencies

### Orchestration
- **Docker Compose**: Local development
- **Kubernetes**: Production orchestration
- **Service Discovery**: Internal service communication
- **Health Checks**: Container health monitoring

### CI/CD Pipeline
- **Testing**: Automated test execution
- **Security Scanning**: Vulnerability assessment
- **Code Quality**: Linting and formatting
- **Deployment**: Automated deployment pipeline

## Future Enhancements

### Additional Features
- **API Versioning**: Backward compatibility
- **GraphQL**: Alternative query interface
- **WebSocket**: Real-time updates
- **Event Sourcing**: Audit trail and replay

### Operational Improvements
- **Distributed Tracing**: OpenTelemetry integration
- **Circuit Breakers**: Fault tolerance
- **Auto-scaling**: Dynamic resource allocation
- **Blue-Green Deployment**: Zero-downtime deployments

### Security Enhancements
- **OAuth2**: Third-party authentication
- **RBAC**: Role-based access control
- **API Keys**: Service-to-service authentication
- **Audit Logging**: Security event tracking
