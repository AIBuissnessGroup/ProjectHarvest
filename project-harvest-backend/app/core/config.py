"""
Configuration settings for Project Harvest
Uses Pydantic for type-safe configuration management
"""

from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables
    
    Why Pydantic Settings?
    - Type validation (ensures strings are strings, ints are ints, etc.)
    - Automatic loading from .env file
    - Clear error messages if required fields are missing
    """
    
    # ============================================
    # API Configuration
    # ============================================
    API_V1_STR: str = "/api"
    PROJECT_NAME: str = "Project Harvest"
    VERSION: str = "0.1.0"
    
    # CORS - Allow frontend to make requests
    # In production, limit this to specific domains
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:3001",  # Alternative port
        "http://127.0.0.1:3000",
    ]
    
    # ============================================
    # Database Configuration
    # ============================================
    POSTGRES_USER: str = "harvest_user"
    POSTGRES_PASSWORD: Optional[str] = "postgres"  # Optional for local dev
    POSTGRES_DB: str = "harvest"
    POSTGRES_HOST: str = "postgres"  # Docker service name
    POSTGRES_PORT: int = 5432
    
    @property
    def DATABASE_URL(self) -> str:
        """Construct PostgreSQL connection URL"""
        return (
            f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )
    
    # ============================================
    # Redis Configuration (for caching)
    # ============================================
    REDIS_HOST: str = "redis"  # Docker service name
    REDIS_PORT: int = 6379
    
    @property
    def REDIS_URL(self) -> str:
        """Construct Redis connection URL"""
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}"
    
    # ============================================
    # External APIs
    # ============================================
    # Fortnite API base URL
    FORTNITE_API_BASE: str = "https://api.fortnite.com/ecosystem/v1"
    
    # OpenAI API key for ChatGPT integration
    OPENAI_API_KEY: Optional[str] = None  # Optional - needed for ChatGPT features
    
    # ============================================
    # Cache TTL (Time To Live) Settings
    # ============================================
    # How long to cache API responses (in seconds)
    CACHE_TTL_ISLANDS: int = 3600      # 1 hour - island list doesn't change often
    CACHE_TTL_METRICS: int = 1800      # 30 minutes - metrics update more frequently
    CACHE_TTL_PREDICTIONS: int = 7200  # 2 hours - predictions are expensive to compute
    
    # ============================================
    # ML Model Configuration
    # ============================================
    MODEL_PATH: str = "data/models"
    
    # ============================================
    # Rate Limiting
    # ============================================
    RATE_LIMIT_PER_MINUTE: int = 60  # Max requests per minute per IP
    
    class Config:
        """Pydantic configuration"""
        env_file = ".env"  # Load from .env file
        case_sensitive = True  # Environment variable names are case-sensitive


# Create a global settings instance
# This will be imported throughout the application
settings = Settings()

