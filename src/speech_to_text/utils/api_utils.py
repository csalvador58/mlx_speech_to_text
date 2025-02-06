# File: src/speech_to_text/utils/api_utils.py
"""
API utility functions for handling SSE events and response formatting.
Provides shared functionality across API routes.
"""

import json
import logging
from typing import Optional, Dict, Any
from queue import Queue

# Store session queues globally
session_queues: Dict[str, Queue] = {}


def format_sse(
    data: dict, event: Optional[str] = None, retry: Optional[int] = None
) -> str:
    """
    Format data for Server-Sent Events transmission.

    Args:
        data: Data to be sent in the event
        event: Optional event type identifier
        retry: Optional retry timeout in milliseconds

    Returns:
        str: Formatted SSE message
    """
    msg = f"data: {json.dumps(data)}\n"
    if event is not None:
        msg = f"event: {event}\n{msg}"
    if retry is not None:
        msg = f"retry: {retry}\n{msg}"
    return f"{msg}\n"


def create_status_response(
    status: str,
    message: str,
    data: Optional[Dict[str, Any]] = None,
    error: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Create a standardized API response.

    Args:
        status: Response status identifier
        message: Human-readable status message
        data: Optional data payload
        error: Optional error information

    Returns:
        dict: Formatted response dictionary
    """
    response = {"status": status, "message": message}
    if data is not None:
        response["data"] = data
    if error is not None:
        response["error"] = error
    return response


def get_event_type(status: str) -> str:
    """
    Get the appropriate event type for a status.
    
    Args:
        status: Status identifier

    Returns:
        str: Event type for SSE
    """
    if status == "calibrating":
        return "calibration"
    elif status in ["recording", "silence", "processing"]:
        return "recording"
    elif status in ["streaming", "complete", "error"]:
        return status
    return "recording"  # Default event type


def create_status_callback(session_id: str, status_queue: Queue) -> callable:
    """
    Create a status callback function for the given session.

    Args:
        session_id: Unique session identifier
        status_queue: Queue for status events

    Returns:
        callable: Status update callback function
    """

    def status_update(status: str, message: str, progress: Optional[int] = None):
        """Send status updates to SSE stream."""
        try:
            event_type = get_event_type(status)
            status_queue.put(
                {
                    "event": event_type,
                    "data": {
                        "session_id": session_id,
                        "status": status,
                        "message": message,
                        "progress": progress,
                    },
                }
            )
            logging.debug(f"Status update queued for session {session_id}: {status}")
        except Exception as e:
            logging.error(
                f"Failed to queue status update for session {session_id}: {e}"
            )

    return status_update


def cleanup_session(session_id: Optional[str] = None) -> None:
    """
    Clean up session resources.

    Args:
        session_id: Optional specific session to clean up.
                   If None, attempt to clean up all sessions.
    """
    if session_id:
        if session_id in session_queues:
            del session_queues[session_id]
            logging.info(f"Cleaned up session: {session_id}")
    else:
        # Clean all sessions
        session_queues.clear()
        logging.info("Cleaned up all sessions")