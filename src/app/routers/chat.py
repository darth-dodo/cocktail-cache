"""Router for Raja chat endpoints.

This module provides endpoints for conversational interaction with Raja,
the AI bartender. Raja provides personality-rich cocktail advice based on
the user's mood, cabinet, and preferences.
"""

import logging

from fastapi import APIRouter, HTTPException

from src.app.models import (
    ChatRequest,
    ChatResponse,
)

logger = logging.getLogger(__name__)

# Create the API router
router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat_with_raja(chat_request: ChatRequest) -> ChatResponse:
    """Send a message to Raja and get a response.

    This is the main chat endpoint for conversational interaction with Raja,
    the AI bartender from Bombay. Raja provides personality-rich cocktail
    advice based on the user's mood, cabinet, and preferences.

    First-time callers should omit session_id to start a new conversation.
    Follow-up messages should include the session_id from the previous response.

    Args:
        chat_request: Chat request with message and optional context.

    Returns:
        ChatResponse with Raja's response and extracted entities.
    """
    from src.app.crews.raja_chat_crew import run_raja_chat

    logger.info(
        f"Chat request: session_id={chat_request.session_id}, "
        f"message_length={len(chat_request.message)}"
    )

    # Run the crew with native async (no thread pool needed)
    response = await run_raja_chat(chat_request)

    logger.info(f"Chat response: session_id={response.session_id}")
    return response


@router.get("/{session_id}/history")
async def get_chat_history(session_id: str) -> dict:
    """Get the conversation history for a chat session.

    Returns the full conversation history including Raja's greeting
    and all subsequent messages.

    Args:
        session_id: The session ID to retrieve history for.

    Returns:
        Dictionary with session info and message history.

    Raises:
        HTTPException: If session is not found.
    """
    from src.app.crews.raja_chat_crew import get_session

    session = get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Chat session not found: {session_id}",
        )

    return {
        "session_id": session.session_id,
        "created_at": session.created_at.isoformat(),
        "last_active": session.last_active.isoformat(),
        "message_count": len(session.history.messages),
        "messages": [
            {
                "id": msg.id,
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
            }
            for msg in session.history.messages
        ],
        "current_mood": session.current_mood,
        "last_recommended_drink": session.last_recommended_drink,
    }


@router.delete("/{session_id}")
async def end_chat_session(session_id: str) -> dict:
    """End a chat session and clean up resources.

    This deletes the session and its history from memory.
    The session_id will no longer be valid for follow-up messages.

    Args:
        session_id: The session ID to delete.

    Returns:
        Confirmation message.

    Raises:
        HTTPException: If session is not found.
    """
    from src.app.crews.raja_chat_crew import delete_session

    if not delete_session(session_id):
        raise HTTPException(
            status_code=404,
            detail=f"Chat session not found: {session_id}",
        )

    return {
        "success": True,
        "message": f"Session {session_id} has been deleted",
    }
