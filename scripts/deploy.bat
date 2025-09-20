@echo off
REM Deployment script for Order API (Windows)
REM Usage: scripts\deploy.bat [environment]

set ENVIRONMENT=%1
if "%ENVIRONMENT%"=="" set ENVIRONMENT=production
echo Deploying to %ENVIRONMENT% environment...

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo Error: Docker is not running
    exit /b 1
)

REM Create .env file if it doesn't exist
if not exist .env (
    echo Creating .env file from template...
    copy env.sample .env
    echo Please update .env file with your production values
    exit /b 1
)

REM Pull latest images
echo Pulling latest images...
docker-compose pull

REM Run database migrations
echo Running database migrations...
docker-compose exec -T api alembic upgrade head

REM Restart services
echo Restarting services...
docker-compose up -d

REM Wait for services to be healthy
echo Waiting for services to be healthy...
timeout /t 30 /nobreak >nul

REM Health check
echo Performing health check...
curl -f http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo Health check failed!
    echo Checking logs...
    docker-compose logs api
    exit /b 1
) else (
    echo Deployment successful!
    echo API is available at: http://localhost:8000
    echo Documentation: http://localhost:8000/docs
    echo Metrics: http://localhost:8000/metrics
)

echo Deployment completed successfully!
