from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from .settings import settings
from .users.api import router as users_router
from .auth.api import router as auth_router
from .holdings.api import router as holdings_router
from .companies.api import router as companies_router
from .departments.api import router as departments_router
from .knowledge_base.api import router as knowledge_base_router
from .smtp.api import router as emails_router
from .smtp.service import init_email_service

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
app.include_router(departments_router)
app.include_router(knowledge_base_router)
app.include_router(emails_router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup"""
    logger = logging.getLogger(__name__)

    # Initialize email service if SMTP is configured
    if settings.SMTP_USERNAME and settings.SMTP_PASSWORD:
        try:
            init_email_service(
                smtp_host=settings.SMTP_HOST,
                smtp_port=settings.SMTP_PORT,
                smtp_username=settings.SMTP_USERNAME,
                smtp_password=settings.SMTP_PASSWORD,
                smtp_use_tls=settings.SMTP_USE_TLS,
                sender_email=settings.SMTP_SENDER_EMAIL or settings.SMTP_USERNAME,
                sender_name=settings.SMTP_SENDER_NAME
            )
            logger.info("Email service initialized successfully")
        except Exception as e:
            logger.warning(f"Failed to initialize email service: {str(e)}")
    else:
        logger.warning("SMTP credentials not configured. Email service will not be available.")


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to FreedomAIAdmin API",
        "version": settings.API_VERSION,
        "docs": "/docs",
        "health": "/users/health"
    }