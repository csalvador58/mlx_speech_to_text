# File: src/speech_to_text/api/connect_status.py

import logging
from flask import Blueprint, Response, stream_with_context
from queue import Empty

from speech_to_text.config.settings import SSE_RETRY_TIMEOUT
from speech_to_text.utils.api_utils import (
    format_sse,
    session_queues,
    cleanup_session
)

status_bp = Blueprint("connect_status", __name__)

@status_bp.route("/<session_id>", methods=["GET"])
def stream_status(session_id: str):
    """Stream status updates for the recording process."""
    def generate():
        try:
            # Get queue for this session
            queue = session_queues.get(session_id)
            if not queue:
                yield format_sse({
                    "session_id": session_id,
                    "status": "error",
                    "message": "Session not found",
                    "progress": None
                })
                return

            # Set SSE retry timeout
            yield format_sse({}, retry=SSE_RETRY_TIMEOUT)
            
            # Stream status updates from queue
            while True:
                try:
                    event_data = queue.get(timeout=30)  # 30 second timeout
                    yield format_sse(
                        data=event_data["data"],
                        event=event_data["event"]
                    )
                    
                    # If status is complete or error, clean up
                    if event_data["data"]["status"] in ["complete", "error"]:
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
            yield format_sse({
                "session_id": session_id,
                "status": "error",
                "message": str(e),
                "progress": None
            })
            cleanup_session(session_id)
    
    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Transfer-Encoding": "chunked",
            "Connection": "keep-alive"
        }
    )