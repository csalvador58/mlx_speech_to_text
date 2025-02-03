# File: src/speech_to_text/api/connect_status.py
"""
Status endpoint for SSE updates during the speech-to-text process.
Handles streaming status updates to clients.
"""

import logging
from flask import Blueprint, Response, jsonify, stream_with_context
from queue import Empty

from speech_to_text.config.settings import SSE_RETRY_TIMEOUT
from speech_to_text.utils.api_utils import format_sse, session_queues, cleanup_session

status_bp = Blueprint("connect_status", __name__)

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


@status_bp.route("/<session_id>", methods=["GET"])
def stream_status(session_id: str):
    """Stream status updates for the recording process."""

    def generate():
        try:
            # Get queue for this session
            queue = session_queues.get(session_id)
            if not queue:
                yield format_sse(
                    {
                        "session_id": session_id,
                        "status": "error",
                        "message": "Session not found",
                        "progress": None,
                    }
                )
                return

            # Set SSE retry timeout
            yield format_sse({}, retry=SSE_RETRY_TIMEOUT)

            # Stream status updates from queue
            while True:
                try:
                    event_data = queue.get(timeout=30)  # 30 second timeout

                    # Validate status data
                    status = event_data["data"]["status"]
                    message = event_data["data"]["message"]
                    progress = event_data["data"].get("progress")

                    if not validate_status_event(status, message, progress):
                        continue

                    # Stream the event
                    yield format_sse(data=event_data["data"], event=event_data["event"])

                    # Handle completion or error
                    if status in ["complete", "error"]:
                        cleanup_session(session_id)
                        break

                except Empty:
                    # Send keepalive
                    yield format_sse({"type": "keepalive"})

        except GeneratorExit:
            logging.info(f"Client disconnected from status stream [{session_id}]")
            cleanup_session(session_id)

        except Exception as e:
            logging.error(f"Error in status stream [{session_id}]: {str(e)}")
            yield format_sse(
                {
                    "session_id": session_id,
                    "status": "error",
                    "message": str(e),
                    "progress": None,
                }
            )
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
    If no update is available, return a default value.
    """
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
        return jsonify(event_data["data"])
    except Empty:
        # No new events
        return jsonify(
            {
                "session_id": session_id,
                "status": "unknown",
                "message": "No new update",
                "progress": None,
            }
        )
