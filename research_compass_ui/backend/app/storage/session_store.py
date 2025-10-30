"""In-memory storage for research sessions."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4


class SessionStore:
    """In-memory store for active research sessions."""

    def __init__(self):
        """Initialize the session store."""
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(
        self,
        query: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create a new research session.

        Args:
            query: The research query
            config: Configuration dictionary

        Returns:
            The created session dictionary
        """
        session_id = str(uuid4())
        timestamp = datetime.now().isoformat()

        session = {
            "session_id": session_id,
            "query": query,
            "status": "initializing",
            "created_at": timestamp,
            "updated_at": timestamp,
            "config": config,
            "messages": [],
            "result": None,
        }

        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a session by ID.

        Args:
            session_id: The session ID

        Returns:
            The session dictionary or None if not found
        """
        return self._sessions.get(session_id)

    def update_session(
        self,
        session_id: str,
        status: Optional[str] = None,
        result: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Update a session's status and/or result.

        Args:
            session_id: The session ID
            status: New status (optional)
            result: Result data (optional)

        Returns:
            True if updated, False if session not found
        """
        session = self._sessions.get(session_id)
        if not session:
            return False

        if status is not None:
            session["status"] = status
        if result is not None:
            session["result"] = result

        session["updated_at"] = datetime.now().isoformat()
        return True

    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session.

        Args:
            session_id: The session ID

        Returns:
            True if deleted, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False

    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all sessions.

        Returns:
            List of all session dictionaries
        """
        return list(self._sessions.values())

    def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists.

        Args:
            session_id: The session ID

        Returns:
            True if exists, False otherwise
        """
        return session_id in self._sessions


# Global session store instance
session_store = SessionStore()
