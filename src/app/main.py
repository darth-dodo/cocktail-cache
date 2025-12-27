"""FastAPI application entry point for Cocktail Cache."""

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.app.config import get_settings

# Application paths
APP_DIR = Path(__file__).parent
TEMPLATES_DIR = APP_DIR / "templates"
STATIC_DIR = APP_DIR / "static"

# Initialize settings
settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title="Cocktail Cache",
    description="AI-powered cocktail recommendation system",
    version="0.1.0",
    debug=settings.DEBUG,
)

# Mount static files
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Initialize Jinja2 templates
templates = Jinja2Templates(directory=TEMPLATES_DIR)


@app.get("/health", response_class=JSONResponse)
async def health_check() -> dict:
    """Health check endpoint for monitoring and orchestration."""
    return {
        "status": "healthy",
        "environment": settings.APP_ENV,
        "version": "0.1.0",
    }


@app.get("/")
async def root() -> dict:
    """Root endpoint."""
    return {
        "message": "Welcome to Cocktail Cache",
        "docs": "/docs",
        "health": "/health",
    }
