#!/bin/bash

# Deployment script for Order API
# Usage: ./scripts/deploy.sh [environment]

set -e

ENVIRONMENT=${1:-production}
echo "Deploying to $ENVIRONMENT environment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "Error: Docker is not running"
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp env.sample .env
    echo "Please update .env file with your production values"
    exit 1
fi

# Pull latest images
echo "Pulling latest images..."
docker-compose pull

# Run database migrations
echo "Running database migrations..."
docker-compose exec -T api alembic upgrade head

# Restart services
echo "Restarting services..."
docker-compose up -d

# Wait for services to be healthy
echo "Waiting for services to be healthy..."
sleep 30

# Health check
echo "Performing health check..."
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ Deployment successful!"
    echo "API is available at: http://localhost:8000"
    echo "Documentation: http://localhost:8000/docs"
    echo "Metrics: http://localhost:8000/metrics"
else
    echo "❌ Health check failed!"
    echo "Checking logs..."
    docker-compose logs api
    exit 1
fi

echo "Deployment completed successfully!"
