"""API routes for research operations."""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect

from app.core.config import settings
from app.models.schemas import ResearchRequest, SessionInfo
from app.services.research_service import research_service
from app.storage.session_store import session_store

router = APIRouter(prefix="/api/research", tags=["research"])


@router.post("/start", response_model=SessionInfo)
async def start_research(request: ResearchRequest) -> SessionInfo:
    """
    Start a new research session.

    Args:
        request: Research request with query and configuration

    Returns:
        Session information

    Raises:
        HTTPException: If research_compass_core is not available
    """
    if not research_service.is_available():
        raise HTTPException(
            status_code=500,
            detail="research_compass_core not available",
        )

    # Create session in store
    session = session_store.create_session(
        query=request.query,
        config=request.model_dump(),
    )

    print(f"✓ Created session {session['session_id']}")
    print(f"   Query: {request.query[:50]}...")
    print(f"   Status: {session['status']}")

    return SessionInfo(
        session_id=session["session_id"],
        query=session["query"],
        status=session["status"],
        created_at=session["created_at"],
        updated_at=session["updated_at"],
        config=session["config"],
    )


@router.websocket("/stream/{session_id}")
async def research_stream(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for streaming research progress.

    Args:
        websocket: WebSocket connection
        session_id: Session ID to stream

    The WebSocket sends JSON messages with the following types:
    - status: Status update
    - progress: Progress update during research
    - complete: Research completed with results
    - error: Error occurred
    """
    await websocket.accept()
    print(f"🔌 WebSocket connected for session {session_id}")

    # Check if session exists
    if not session_store.session_exists(session_id):
        print(f"❌ Session {session_id} not found in WebSocket!")
        all_sessions = session_store.list_sessions()
        print(f"   Available sessions: {[s['session_id'] for s in all_sessions]}")
        await websocket.send_json({
            "type": "error",
            "message": "Session not found",
        })
        await websocket.close()
        return

    session = session_store.get_session(session_id)
    config_data = session["config"]
    print(f"✓ Session {session_id} found, starting research...")

    try:
        # Update session status to running
        session_store.update_session(session_id, status="running")

        await websocket.send_json({
            "type": "status",
            "status": "running",
            "message": "Starting research...",
        })

        # Create configuration
        configuration = research_service.create_configuration(
            search_api=config_data.get("search_api", "arxiv"),
            research_model=config_data.get("research_model", "openai:gpt-4o"),
            summarization_model=config_data.get("summarization_model", "openai:gpt-4o-mini"),
            max_researcher_iterations=config_data.get("max_researcher_iterations", 6),
            max_concurrent_research_units=config_data.get("max_concurrent_research_units", 5),
            export_formats=config_data.get("export_formats", []),
            export_directory=settings.export_directory,
            allow_clarification=config_data.get("allow_clarification", True),
        )

        # Send initialization message
        await websocket.send_json({
            "type": "progress",
            "stage": "initialization",
            "message": "Initializing research agent...",
        })

        # Run research and stream updates
        all_events = []
        accumulated_data = {}

        async for event in research_service.run_research(
            query=session["query"],
            session_id=session_id,
            configuration=configuration,
        ):
            # Send progress update to client
            await websocket.send_json({
                "type": "progress",
                "stage": "researching",
                "event": str(event),
                "message": "Research in progress...",
            })

            # Accumulate data from all events
            all_events.append(event)
            if isinstance(event, dict):
                for node_name, node_data in event.items():
                    if isinstance(node_data, dict):
                        # Merge data from this node
                        accumulated_data.update(node_data)

        # Extract and send final result from accumulated data
        print(f"📊 Research completed, processing results...")
        print(f"   Total events: {len(all_events)}")
        print(f"   Accumulated data keys: {list(accumulated_data.keys())}")

        if accumulated_data:
            # Try to extract from accumulated data
            extracted_result = {
                "final_report": accumulated_data.get("final_report"),
                "exported_files": accumulated_data.get("exported_files", []),
            }

            if extracted_result.get("final_report"):
                print(f"✅ Final report found! Length: {len(extracted_result['final_report'])} chars")
                print(f"   Exported files: {len(extracted_result.get('exported_files', []))}")

                session_store.update_session(
                    session_id,
                    status="completed",
                    result=extracted_result,
                )

                await websocket.send_json({
                    "type": "complete",
                    "status": "completed",
                    "result": extracted_result,
                })
            else:
                session_store.update_session(session_id, status="failed")
                await websocket.send_json({
                    "type": "error",
                    "message": "Research failed - no result generated",
                })
        else:
            session_store.update_session(session_id, status="failed")
            await websocket.send_json({
                "type": "error",
                "message": "Research failed - no result generated",
            })

    except WebSocketDisconnect:
        session_store.update_session(session_id, status="disconnected")
    except Exception as e:
        session_store.update_session(session_id, status="error")
        await websocket.send_json({
            "type": "error",
            "message": str(e),
        })
    finally:
        await websocket.close()
