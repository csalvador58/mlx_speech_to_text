# File: src/speech_to_text/utils/api_utils.py
"""
API utility functions for handling SSE events and response formatting.
Provides shared functionality across API routes with enhanced document context support.
"""

import json
import logging
from typing import Optional, Dict, Any
from queue import Queue
from pathlib import Path

# Store session queues globally
session_queues: Dict[str, Queue] = {}

# Enhanced error types
ERROR_TYPES = {
    "invalid_parameter": "Invalid request parameters",
    "chat_error": "Chat session errors",
    "transcription_error": "Audio processing errors",
    "server_error": "Internal server errors",
    "document_error": "Document processing errors",
    "validation_error": "Input validation errors"
}

# Status types with descriptions
STATUS_TYPES = {
    "calibrating": "Initial microphone calibration",
    "recording": "Active recording",
    "silence": "Silence detection (includes progress 0-100)",
    "processing": "Processing audio",
    "doc_loading": "Loading document context",
    "doc_processing": "Processing with document context",
    "streaming": "Playing voice response",
    "complete": "Operation complete",
    "error": "Error occurred"
}

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
    doc_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a standardized API response with document context support.

    Args:
        status: Response status identifier
        message: Human-readable status message
        data: Optional data payload
        error: Optional error information
        doc_path: Optional document path for context

    Returns:
        dict: Formatted response dictionary
    """
    response = {"status": status, "message": message}
    
    if data is not None:
        response["data"] = data
        # Add document context to data if provided
        if doc_path:
            response["data"]["doc_path"] = str(doc_path)
    
    if error is not None:
        if error.get("type") not in ERROR_TYPES:
            logging.warning(f"Unknown error type: {error.get('type')}")
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
    # Document-specific events
    if status in ["doc_loading", "doc_processing"]:
        return "processing"
    
    # Standard events
    if status == "calibrating":
        return "calibration"
    elif status in ["recording", "silence", "processing"]:
        return "recording"
    elif status in ["streaming", "complete", "error"]:
        return status
    
    # Default event type
    logging.warning(f"Unknown status type: {status}")
    return "recording"


def validate_status_type(status: str) -> bool:
    """
    Validate a status type against known types.

    Args:
        status: Status type to validate

    Returns:
        bool: True if valid status type
    """
    if status not in STATUS_TYPES:
        logging.warning(f"Unknown status type: {status}")
        return False
    return True


def create_document_error(
    error_message: str,
    doc_path: Optional[str] = None
) -> Dict[str, str]:
    """
    Create a standardized document error response.

    Args:
        error_message: Description of the error
        doc_path: Optional path to document that caused error

    Returns:
        dict: Formatted error dictionary
    """
    error = {
        "type": "document_error",
        "description": error_message
    }
    
    if doc_path:
        error["document"] = str(doc_path)
    
    return error


def create_status_callback(session_id: str, status_queue: Queue) -> callable:
    """
    Create a status callback function for the given session.

    Args:
        session_id: Unique session identifier
        status_queue: Queue for status events

    Returns:
        callable: Status update callback function
    """

    def status_update(
        status: str,
        message: str,
        progress: Optional[int] = None,
        doc_path: Optional[str] = None
    ):
        """
        Send status updates to SSE stream.
        
        Args:
            status: Status identifier
            message: Status message
            progress: Optional progress value
            doc_path: Optional document path for context
        """
        try:
            # Validate status type
            if not validate_status_type(status):
                status = "error"
                message = f"Invalid status type: {status}"

            # Create status data
            status_data = {
                "session_id": session_id,
                "status": status,
                "message": message,
                "progress": progress
            }

            # Add document context if provided
            if doc_path:
                status_data["doc_path"] = str(doc_path)

            # Get event type and queue update
            event_type = get_event_type(status)
            status_queue.put(
                {
                    "event": event_type,
                    "data": status_data
                }
            )

            logging.debug(
                f"Status update queued for session {session_id}: "
                f"{status} - {message}"
            )

        except Exception as e:
            error_msg = f"Failed to queue status update for session {session_id}: {e}"
            logging.error(error_msg)
            # Try to queue error status
            try:
                status_queue.put({
                    "event": "error",
                    "data": {
                        "session_id": session_id,
                        "status": "error",
                        "message": error_msg,
                        "progress": None
                    }
                })
            except:
                pass  # If error queuing fails, just log it

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