from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .settings import settings
from .users.api import router as users_router
from .auth.api import router as auth_router
from .holdings.api import router as holdings_router
from .companies.api import router as companies_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Admin Freedom API for user management and data analysis"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users_router)
app.include_router(auth_router)
app.include_router(holdings_router)
app.include_router(companies_router)

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to FreedomAIAdmin API",
        "version": settings.API_VERSION,
        "docs": "/docs",
        "health": "/users/health"
    }