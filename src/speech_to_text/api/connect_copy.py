# File: src/speech_to_text/api/connect_copy.py
"""
Copy endpoint for the speech-to-text application.
Immediately returns a session ID while transcription is performed asynchronously,
and status updates are sent via the SSE endpoint.
"""

import logging
import uuid
from flask import Blueprint, jsonify
from queue import Queue
from threading import Event, Thread

from speech_to_text.audio.recorder import AudioRecorder
from speech_to_text.transcriber.whisper import WhisperTranscriber
from speech_to_text.utils import handle_transcription
from speech_to_text.utils.api_utils import (
    create_status_response,
    create_status_callback,
    session_queues,
    cleanup_session,
)

copy_bp = Blueprint("connect_copy", __name__)


@copy_bp.route("/start", methods=["POST"])
def start_recording():
    """
    Start recording audio for transcription and clipboard copy.
    Immediately returns a session ID while transcription is performed asynchronously,
    and status updates are sent via the SSE endpoint.
    """
    session_id = str(uuid.uuid4())
    stop_event = Event()

    # Create status queue for this session
    status_queue = Queue()
    session_queues[session_id] = status_queue

    try:
        # Initialize handlers
        recorder = AudioRecorder()
        transcriber = WhisperTranscriber()

        # Create status callback to queue SSE events
        status_callback = create_status_callback(session_id, status_queue)

        # Start the transcription process in a background thread
        def background_transcription():
            with recorder:
                success, error_message, response_data = handle_transcription(
                    recorder,
                    transcriber,
                    copy_to_clipboard=True,
                    output_file=None,
                    use_kokoro=False,
                    use_llm=False,
                    chat_handler=None,
                    stream_to_speakers=False,
                    save_to_file=False,
                    optimize_voice=False,
                    status_callback=status_callback,
                    stop_event=stop_event,
                )
                if not success and error_message:
                    logging.error(
                        f"Transcription error in background task: {error_message}"
                    )

        Thread(target=background_transcription, daemon=True).start()

        # Immediately return the session ID
        return jsonify(
            create_status_response(
                "success",
                "Copy session started",
                data={"session_id": session_id},
            )
        ), 200

    except Exception as e:
        logging.error(f"Error starting copy session: {str(e)}")
        cleanup_session(session_id)
        return jsonify(
            create_status_response(
                "error",
                "Internal server error",
                error={"type": "server_error", "description": str(e)},
            )
        ), 500