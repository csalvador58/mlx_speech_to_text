# File: src/speech_to_text/api/connect_status.py
"""
Status endpoint for SSE updates during the speech-to-text process.
Handles streaming status updates to clients with consistent event formatting.
"""

import logging
from flask import Blueprint, Response, jsonify, stream_with_context
from queue import Empty, Queue
from threading import Lock
from typing import Dict, Optional

from speech_to_text.config.settings import SSE_RETRY_TIMEOUT, SSE_KEEPALIVE_TIMEOUT
from speech_to_text.utils.api_utils import format_sse, session_queues, cleanup_session

status_bp = Blueprint("connect_status", __name__)

# Store last status per session
last_status: Dict[str, dict] = {}
status_lock = Lock()

VALID_STATUS_TYPES = {
    "calibrating": "Starting background calibration...",
    "recording": "Ready for speech...",
    "silence": "Detecting silence...",  # Includes progress 0-100%
    "processing": "Processing your request...",
    "streaming": "Playing response audio...",
    "complete": "",  # Message varies by mode
    "error": "",  # Error message
}

def validate_status_event(status: str, message: str, progress: int = None) -> bool:
    """
    Validate status event data.

    Args:
        status: Status type
        message: Status message
        progress: Optional progress value

    Returns:
        bool: True if valid, False otherwise
    """
    if status not in VALID_STATUS_TYPES:
        logging.warning(f"Invalid status type received: {status}")
        return False

    # Special validation for silence progress
    if status == "silence" and (progress is None or not 0 <= progress <= 100):
        logging.warning(f"Invalid silence progress value: {progress}")
        return False

    return True

def update_last_status(session_id: str, status_data: dict) -> None:
    """Thread-safe update of last status."""
    with status_lock:
        last_status[session_id] = status_data

def get_last_status(session_id: str) -> Optional[dict]:
    """Thread-safe retrieval of last status."""
    with status_lock:
        return last_status.get(session_id)

@status_bp.route("/<session_id>", methods=["GET"])
def stream_status(session_id: str):
    """Stream status updates for the recording process."""

    def generate():
        try:
            # Get queue for this session
            queue = session_queues.get(session_id)
            if not queue:
                status_data = {
                    "session_id": session_id,
                    "status": "error",
                    "message": "Session not found",
                    "progress": None,
                }
                update_last_status(session_id, status_data)
                yield format_sse(status_data)
                return

            # Set SSE retry timeout
            yield format_sse({}, retry=SSE_RETRY_TIMEOUT)

            # Stream status updates from queue
            while True:
                try:
                    event_data = queue.get(timeout=SSE_KEEPALIVE_TIMEOUT)
                    
                    # Validate status data
                    status = event_data["data"]["status"]
                    message = event_data["data"]["message"]
                    progress = event_data["data"].get("progress")

                    if not validate_status_event(status, message, progress):
                        continue

                    # Update last known status
                    update_last_status(session_id, event_data["data"])
                    
                    # Stream the event
                    yield format_sse(data=event_data["data"], event=event_data["event"])

                    # Handle completion or error
                    if status in ["complete", "error"]:
                        cleanup_session(session_id)
                        break

                except Empty:
                    # Get last known status for keepalive
                    current_status = get_last_status(session_id)
                    if current_status:
                        # Send keepalive with current status preserved
                        keepalive_data = {
                            "session_id": session_id,
                            "status": current_status["status"],
                            "message": current_status["message"],
                            "progress": current_status.get("progress")
                        }
                        yield format_sse(keepalive_data)
                    else:
                        # Fallback if no status available
                        yield format_sse({
                            "session_id": session_id,
                            "status": "unknown",
                            "message": "No status available",
                            "progress": None
                        })

        except GeneratorExit:
            logging.info(f"Client disconnected from status stream [{session_id}]")
            cleanup_session(session_id)

        except Exception as e:
            error_data = {
                "session_id": session_id,
                "status": "error",
                "message": str(e),
                "progress": None,
            }
            update_last_status(session_id, error_data)
            yield format_sse(error_data)
            logging.error(f"Error in status stream [{session_id}]: {str(e)}")
            cleanup_session(session_id)

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Transfer-Encoding": "chunked",
            "Connection": "keep-alive",
        },
    )

@status_bp.route("/current/<session_id>", methods=["GET"])
def current_status(session_id: str):
    """
    Return the most recent status update for a session.
    If no recent update is available, returns the last known status.
    """
    # First check if session exists
    queue = session_queues.get(session_id)
    if not queue:
        return jsonify(
            {
                "session_id": session_id,
                "status": "error",
                "message": "Session not found",
                "progress": None,
            }
        ), 404

    try:
        # Try to get latest update without blocking
        event_data = queue.get_nowait()
        update_last_status(session_id, event_data["data"])
        return jsonify(event_data["data"])
    except Empty:
        # Return last known status if available
        last_known = get_last_status(session_id)
        if last_known:
            return jsonify(last_known)
        
        # Fallback if no status is available
        return jsonify(
            {
                "session_id": session_id,
                "status": "unknown",
                "message": "No status available",
                "progress": None,
            }
        )