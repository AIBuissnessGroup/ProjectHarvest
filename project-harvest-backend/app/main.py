"""
Project Harvest - Main FastAPI Application
==========================================
Backend API for Fortnite Creative Island Analytics
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.models.island import HealthCheck

# ============================================
# Initialize FastAPI App
# ============================================

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Analytics API for Fortnite Creative Islands - Track metrics, predict performance, and get AI insights",
    version="0.1.0",
    docs_url="/api/docs",  # Swagger UI
    redoc_url="/api/redoc",  # ReDoc
)


# ============================================
# CORS Middleware
# ============================================
# Allows frontend (Next.js) to communicate with backend

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js dev server
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        # Production domains
        "https://*.vercel.app",  # Vercel preview deployments
        "https://project-harvest.vercel.app",  # Main Vercel domain (update after deployment)
        "https://projectharvest.vercel.app",
        "https://harvest-ui.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
    allow_origin_regex=r"https://.*\.vercel\.app",  # Allow all Vercel subdomains
)


# ============================================
# Root Endpoint
# ============================================

@app.get("/")
async def root():
    """
    Root endpoint - API welcome message
    """
    return {
        "message": "🌾 Project Harvest API",
        "version": "0.1.0",
        "docs": "/api/docs",
        "health": "/api/health"
    }


# ============================================
# Health Check Endpoint
# ============================================

@app.get("/api/health", response_model=HealthCheck)
async def health_check():
    """
    Health check endpoint
    
    Used by Docker, monitoring tools, and frontend to verify API is running
    """
    return HealthCheck(
        status="healthy",
        version="0.1.0"
    )


# ============================================
# API Routes
# ============================================

from app.api.routes import islands, analytics, chat

app.include_router(islands.router)
app.include_router(analytics.router)
app.include_router(chat.router)


# ============================================
# Startup/Shutdown Events
# ============================================

@app.on_event("startup")
async def startup_event():
    """
    Run on application startup
    """
    from app.services.ml_service import ml_service
    
    print("🚀 Project Harvest API starting up...")
    print(f"📊 API available at: http://localhost:8000")
    print(f"📚 Docs available at: http://localhost:8000/api/docs")
    
    # ML models are loaded automatically in ml_service.__init__
    print("🤖 ML models loaded on initialization")
    
    # Check chat service
    print("💬 Checking AI chat service...")
    if settings.GEMINI_API_KEY:
        print("✅ Google Gemini configured and ready!")
    else:
        print("⚠️  GEMINI_API_KEY not set - AI chat features will not be available")


@app.on_event("shutdown")
async def shutdown_event():
    """
    Run on application shutdown
    """
    print("👋 Project Harvest API shutting down...")

