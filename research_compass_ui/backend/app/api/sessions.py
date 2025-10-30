"""API routes for session management."""

from typing import List

from fastapi import APIRouter, HTTPException

from app.models.schemas import MessageResponse, SessionDetail, SessionInfo
from app.storage.session_store import session_store

router = APIRouter(prefix="/api/research", tags=["sessions"])


@router.get("/sessions", response_model=List[SessionInfo])
async def list_sessions() -> List[SessionInfo]:
    """
    List all research sessions.

    Returns:
        List of session information
    """
    sessions = session_store.list_sessions()
    return [
        SessionInfo(
            session_id=session["session_id"],
            query=session["query"],
            status=session["status"],
            created_at=session["created_at"],
            updated_at=session["updated_at"],
            config=session["config"],
        )
        for session in sessions
    ]


@router.get("/session/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str) -> SessionDetail:
    """
    Get information about a specific research session.

    Args:
        session_id: The session ID

    Returns:
        Detailed session information including results

    Raises:
        HTTPException: If session not found
    """
    session = session_store.get_session(session_id)
    if not session:
        # Debug: List all available sessions
        all_sessions = session_store.list_sessions()
        print(f"❌ Session {session_id} not found!")
        print(f"   Available sessions: {len(all_sessions)}")
        for s in all_sessions:
            print(f"   - {s['session_id']}: {s['status']}")
        raise HTTPException(status_code=404, detail="Session not found")

    return SessionDetail(
        session_id=session["session_id"],
        query=session["query"],
        status=session["status"],
        created_at=session["created_at"],
        updated_at=session["updated_at"],
        config=session["config"],
        result=session.get("result"),
    )


@router.delete("/session/{session_id}", response_model=MessageResponse)
async def delete_session(session_id: str) -> MessageResponse:
    """
    Delete a research session.

    Args:
        session_id: The session ID

    Returns:
        Success message

    Raises:
        HTTPException: If session not found
    """
    deleted = session_store.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Session not found")

    return MessageResponse(message="Session deleted successfully")
