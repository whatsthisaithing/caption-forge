"""CaptionFoundry FastAPI Application."""

import sys
import io
import time
import traceback
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse

from .config import get_settings, PROJECT_ROOT
from .database import init_db, close_db
from .logging_config import get_logger, setup_logging
from .api import (
    folders_router,
    datasets_router,
    captions_router,
    files_router,
    vision_router,
    export_router,
    system_router,
)
from . import __version__

logger = get_logger("captionfoundry.main")


def check_logging_initialized():
    """Check if logging was initialized by app.py, if not set up basic logging."""
    import logging
    root = logging.getLogger()
    if not root.handlers:
        # Not running via app.py, set up basic logging
        setup_logging(level="DEBUG")
        logger.info("Logging initialized by main.py (server-only mode)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    check_logging_initialized()
    logger.info(f"Starting CaptionFoundry v{__version__}")
    
    # Ensure data directories exist
    settings = get_settings()
    (PROJECT_ROOT / settings.thumbnails.cache_path).mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / settings.export.staging_path).mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "data" / "caption_jobs").mkdir(parents=True, exist_ok=True)
    (PROJECT_ROOT / "data" / "logs").mkdir(parents=True, exist_ok=True)
    
    # Initialize database
    init_db()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    close_db()
    logger.info("CaptionFoundry shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="CaptionFoundry",
    description="LORA Dataset Management System - Manage image datasets with AI-powered captioning",
    version=__version__,
    lifespan=lifespan,
)

# Configure CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local use
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler to log all unhandled errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Log all unhandled exceptions to the debug log."""
    error_logger = get_logger("captionfoundry.errors")
    error_logger.error(f"Unhandled exception on {request.method} {request.url.path}")
    error_logger.error(f"Exception type: {type(exc).__name__}")
    error_logger.error(f"Exception message: {str(exc)}")
    error_logger.error(f"Traceback:\n{traceback.format_exc()}")
    
    # Return a generic error response
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"}
    )


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all API requests with timing."""
    # Skip logging for static files and thumbnails
    path = request.url.path
    if path.startswith("/api"):
        request_logger = get_logger("captionfoundry.api.requests")
        start_time = time.time()
        
        # Log request (using ASCII-safe arrows)
        request_logger.debug(f"-> {request.method} {path}")
        
        # Process request
        response = await call_next(request)
        
        # Log response with timing (using ASCII-safe symbols)
        duration_ms = (time.time() - start_time) * 1000
        status_symbol = "[OK]" if response.status_code < 400 else "[ERR]"
        request_logger.debug(f"<- {status_symbol} {request.method} {path} [{response.status_code}] {duration_ms:.1f}ms")
        
        return response
    else:
        return await call_next(request)


# Include API routers
app.include_router(folders_router, prefix="/api")
app.include_router(datasets_router, prefix="/api")
app.include_router(captions_router, prefix="/api")
app.include_router(files_router, prefix="/api")
app.include_router(vision_router, prefix="/api")
app.include_router(export_router, prefix="/api")
app.include_router(system_router, prefix="/api")

# Serve static frontend files
frontend_dir = PROJECT_ROOT / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")


@app.get("/api")
def api_root():
    """API root endpoint."""
    return {
        "name": "CaptionFoundry API",
        "version": __version__,
        "docs_url": "/docs",
    }
