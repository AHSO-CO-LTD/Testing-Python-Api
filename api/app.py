from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging
import sys
import os

if getattr(sys, "frozen", False):
    _api_dir = os.path.dirname(sys.executable)
else:
    _api_dir = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, os.path.join(_api_dir, "routers"))
sys.path.insert(0, os.path.join(os.path.dirname(_api_dir), "backend", "AI"))

# Initialize QApplication before importing Qt-dependent modules
from PyQt5.QtWidgets import QApplication

qt_app = QApplication.instance() or QApplication(sys.argv)

import OCR_AI_router
from OCR import OCR

LOG_DIR = os.path.join(_api_dir, "backend", "logs")
print(f"Log directory: {LOG_DIR}")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOG_DIR, "api.log")),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="VisionCenter OCR API",
    description="REST API for VisionCenter OCR",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Global services
ocr_ai = None


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global ocr_ai

    logger.info("Starting VisionCenter API...")

    try:
        # Initialize OCR AI service
        ocr_ai = OCR()
        logger.info("OCR AI service initialized")

        # Store in app state
        app.state.ocr_ai = ocr_ai

        logger.info("API startup complete")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise


# Exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "detail": str(exc),
        },
    )


# Health check endpoint
@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {"service": "VisionCenter AI API", "version": "1.0.0", "status": "running"}


# Include routers
app.include_router(OCR_AI_router.router, prefix="/api/v1/ai", tags=["AI"])
