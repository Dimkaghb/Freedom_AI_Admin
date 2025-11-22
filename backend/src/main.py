from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
import time

from .settings import settings
from .database import get_db_manager, close_database_connection
from .users.api import router as users_router
from .auth.api import router as auth_router
from .holdings.api import router as holdings_router
from .companies.api import router as companies_router
from .departments.api import router as departments_router
from .dashboard.api import router as dashboard_router
from .knowledge_base.api import router as knowledge_base_router
from .smtp.api import router as emails_router
from .smtp.service import init_email_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description="Admin Freedom API for user management and data analysis"
)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()

    # Log incoming request
    logger.info(f"→ {request.method} {request.url.path}")

    try:
        response = await call_next(request)
        process_time = time.time() - start_time

        # Log response
        logger.info(
            f"← {request.method} {request.url.path} "
            f"Status: {response.status_code} "
            f"Time: {process_time:.3f}s"
        )

        return response
    except Exception as e:
        logger.error(f"✗ {request.method} {request.url.path} Error: {str(e)}")
        raise

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
app.include_router(dashboard_router)
app.include_router(knowledge_base_router)
app.include_router(emails_router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup"""

    logger.info("=" * 60)
    logger.info("🚀 Starting FreedomAIAdmin API Server")
    logger.info("=" * 60)

    # Initialize MongoDB connection pool
    try:
        db_manager = get_db_manager()
        conn_info = db_manager.get_connection_info()
        logger.info(f"✅ MongoDB connection pool initialized")
        logger.info(f"   Database: {conn_info.get('database')}")
        logger.info(f"   MongoDB version: {conn_info.get('mongodb_version')}")
        logger.info(f"   Pool size: {conn_info.get('max_pool_size')} connections")
    except Exception as e:
        logger.error(f"❌ Failed to initialize MongoDB: {str(e)}")
        raise

    # Log registered routes
    logger.info("📍 Registered routes:")
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            for method in route.methods:
                routes.append(f"  {method:6s} {route.path}")

    # Sort and log routes
    for route in sorted(set(routes)):
        logger.info(route)

    logger.info("=" * 60)

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
            logger.info("✅ Email service initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️  Failed to initialize email service: {str(e)}")
    else:
        logger.warning("⚠️  SMTP credentials not configured. Email service will not be available.")

    logger.info("=" * 60)
    logger.info("✨ Server ready to accept connections")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    logger.info("=" * 60)
    logger.info("🛑 Shutting down FreedomAIAdmin API Server")
    logger.info("=" * 60)

    # Close MongoDB connection
    try:
        close_database_connection()
        logger.info("✅ MongoDB connection closed")
    except Exception as e:
        logger.error(f"❌ Error closing MongoDB connection: {str(e)}")

    logger.info("=" * 60)
    logger.info("👋 Server shutdown complete")
    logger.info("=" * 60)


@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Welcome to FreedomAIAdmin API",
        "version": settings.API_VERSION,
        "docs": "/docs",
        "health": "/users/health"
    }