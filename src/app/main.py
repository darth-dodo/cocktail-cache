"""FastAPI application entry point for Cocktail Cache."""

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.app.config import get_settings
from src.app.routers import api_router

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

# Configure CORS middleware for development
# In production, restrict origins to your actual frontend domains
cors_origins = ["*"] if settings.is_development else []
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Include API router
app.include_router(api_router, prefix="/api")

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


@app.get("/", response_class=HTMLResponse)
async def root(request: Request) -> HTMLResponse:
    """Render the main cocktail recommendation interface."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )
