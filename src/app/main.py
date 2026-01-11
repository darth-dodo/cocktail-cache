"""FastAPI application entry point for Cocktail Cache."""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.app.config import get_settings
from src.app.routers import api_router
from src.app.services.data_loader import load_all_drinks

logger = logging.getLogger(__name__)

# Application paths
APP_DIR = Path(__file__).parent
TEMPLATES_DIR = APP_DIR / "templates"
STATIC_DIR = APP_DIR / "static"

# Initialize settings
settings = get_settings()


async def session_cleanup_task() -> None:
    """Background task to clean up expired sessions.

    Runs periodically to remove sessions that have exceeded their TTL.
    This prevents memory leaks from unbounded session storage.
    """
    from src.app.crews.raja_chat_crew import (
        cleanup_expired_chat_sessions,
        get_chat_session_count,
    )
    from src.app.routers.flow import cleanup_expired_sessions, get_session_count

    logger.info(
        f"Session cleanup task started "
        f"(interval: {settings.SESSION_CLEANUP_INTERVAL_SECONDS}s, "
        f"TTL: {settings.SESSION_TTL_SECONDS}s)"
    )

    while True:
        try:
            await asyncio.sleep(settings.SESSION_CLEANUP_INTERVAL_SECONDS)

            # Clean up flow sessions
            flow_cleaned = cleanup_expired_sessions()

            # Clean up chat sessions
            chat_cleaned = cleanup_expired_chat_sessions()

            # Log summary if any sessions were cleaned
            total_cleaned = flow_cleaned + chat_cleaned
            if total_cleaned > 0:
                logger.info(
                    f"Session cleanup completed: "
                    f"removed {flow_cleaned} flow + {chat_cleaned} chat sessions. "
                    f"Active: {get_session_count()} flow, {get_chat_session_count()} chat"
                )

        except asyncio.CancelledError:
            logger.info("Session cleanup task cancelled")
            break
        except Exception:
            logger.exception("Error in session cleanup task")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan resources.

    Creates a shared ThreadPoolExecutor for running blocking operations
    without creating a new executor per request. Also starts background
    cleanup task for expired sessions.
    """
    # Startup: Create shared executor
    app.state.executor = ThreadPoolExecutor(max_workers=4)

    # Start background cleanup task
    cleanup_task = asyncio.create_task(session_cleanup_task())

    logger.info("Application startup complete")

    yield

    # Shutdown: Cancel cleanup task and clean up executor
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass

    app.state.executor.shutdown(wait=True)
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="Cocktail Cache",
    description="AI-powered cocktail recommendation system",
    version="0.1.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
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
    """Health check endpoint for container orchestration (Kubernetes, Docker).

    Returns a simple health status with no authentication required.
    Useful for liveness and readiness probes.
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
    }


@app.get("/", response_class=HTMLResponse)
async def root(request: Request) -> HTMLResponse:
    """Render the main cocktail recommendation interface."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
    )


@app.get("/browse", response_class=HTMLResponse)
async def browse(request: Request) -> HTMLResponse:
    """Render the drink browse and search interface."""
    return templates.TemplateResponse(
        request=request,
        name="browse.html",
    )


@app.get("/drink/{drink_id}", response_class=HTMLResponse)
async def drink_detail(request: Request, drink_id: str) -> HTMLResponse:
    """Render the drink detail page.

    Args:
        request: The FastAPI request object.
        drink_id: The unique identifier of the drink.

    Returns:
        HTMLResponse with the drink detail template.

    Raises:
        HTTPException: If drink is not found.
    """
    # Validate drink exists before rendering page
    all_drinks = load_all_drinks()
    drink_ids = {d.id for d in all_drinks}

    if drink_id not in drink_ids:
        raise HTTPException(status_code=404, detail=f"Drink not found: {drink_id}")

    return templates.TemplateResponse(
        request=request,
        name="drink.html",
        context={"drink_id": drink_id},
    )


@app.get("/suggest-bottle", response_class=HTMLResponse)
async def suggest_bottle_page(request: Request) -> HTMLResponse:
    """Render the suggest bottle page for recommendations on what to buy."""
    return templates.TemplateResponse(
        request=request,
        name="suggest-bottle.html",
    )


# Custom exception handlers for HTML pages
@app.exception_handler(StarletteHTTPException)
async def custom_http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> Response:
    """Custom HTTP exception handler with Raja's personality for 404 and 500 errors."""
    # For API routes, return JSON
    if request.url.path.startswith("/api/"):
        return await http_exception_handler(request, exc)

    # Handle 404 errors with custom page
    if exc.status_code == 404:
        # Extract drink_id if this was a drink page request
        drink_id = None
        if request.url.path.startswith("/drink/"):
            drink_id = request.url.path.replace("/drink/", "")

        return templates.TemplateResponse(
            request=request,
            name="404.html",
            context={"drink_id": drink_id},
            status_code=404,
        )

    # Handle 500 errors with custom page
    if exc.status_code == 500:
        return templates.TemplateResponse(
            request=request,
            name="500.html",
            status_code=500,
        )

    # Default handler for other HTTP errors
    return await http_exception_handler(request, exc)


@app.exception_handler(Exception)
async def custom_exception_handler(request: Request, exc: Exception) -> Response:
    """Custom exception handler for unhandled exceptions (500 errors)."""
    # For API routes, return JSON
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )

    return templates.TemplateResponse(
        request=request,
        name="500.html",
        status_code=500,
    )
