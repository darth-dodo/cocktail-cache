"""Main API router for cocktail flow endpoints.

This module serves as the central router that includes all sub-routers:
- drinks: Browse and search drink endpoints
- flow: Recommendation flow endpoints
- bottles: Bottle suggestion endpoints
- chat: Raja chat endpoints

Global rate limits protect upstream API quotas (privacy-first, no user tracking):
- /flow: 10/min (LLM calls - expensive)
- /suggest-bottles: 30/min (compute-intensive)
- Static data endpoints: No limit (fast local lookups)
"""

from fastapi import APIRouter

# Import sub-routers
from src.app.routers.bottles import router as bottles_router
from src.app.routers.chat import router as chat_router
from src.app.routers.drinks import ingredients_router
from src.app.routers.drinks import router as drinks_router
from src.app.routers.flow import router as flow_router

# Create the main API router
router = APIRouter()

# Include sub-routers
# Note: drinks_router has prefix="/drinks", so endpoints will be at /api/drinks/...
router.include_router(drinks_router)

# ingredients_router has no prefix, so /ingredients becomes /api/ingredients
router.include_router(ingredients_router)

# flow_router has no prefix, so /flow becomes /api/flow
router.include_router(flow_router)

# bottles_router has no prefix, so /suggest-bottles becomes /api/suggest-bottles
router.include_router(bottles_router)

# chat_router has prefix="/chat", so endpoints will be at /api/chat/...
router.include_router(chat_router)
