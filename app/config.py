from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://app:app@localhost:5432/app"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # JWT
    secret_key: str = "your-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds
    
    # Environment
    environment: str = "development"
    log_level: str = "INFO"
    
    # Prometheus
    prometheus_port: int = 8001
    
    class Config:
        env_file = ".env"


settings = Settings()
