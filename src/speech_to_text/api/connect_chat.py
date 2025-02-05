# File: src/speech_to_text/api/connect_chat.py
"""
Chat endpoint for starting a chat session.
Immediately returns a session ID while transcription is performed asynchronously,
and status updates are sent via the SSE endpoint.
"""

import logging
import uuid
from pathlib import Path
from flask import Blueprint, jsonify, request
from queue import Queue
from threading import Event, Thread

from speech_to_text.audio.recorder import AudioRecorder
from speech_to_text.transcriber.whisper import WhisperTranscriber
from speech_to_text.utils import handle_transcription
from speech_to_text.chat import ChatHandler
from speech_to_text.utils.path_utils import validate_file_path
from speech_to_text.utils.api_utils import (
    create_status_response,
    create_status_callback,
    session_queues,
    cleanup_session,
)

chat_bp = Blueprint("connect_chat", __name__)


@chat_bp.route("/list", methods=["GET"])
def list_chats():
    """
    Retrieve list of available chat sessions.
    Returns a list of chat IDs sorted by modification time (most recent first).
    """
    try:
        # Use ChatHandler to get list of chats
        chat_handler = ChatHandler()
        chat_files = chat_handler.chat_history.get_chat_list()

        return jsonify(
            create_status_response(
                "success",
                "Chat history retrieved successfully",
                data={"chats": chat_files}
            )
        ), 200

    except Exception as e:
        logging.error(f"Error retrieving chat history: {str(e)}")
        return jsonify(
            create_status_response(
                "error",
                "Failed to retrieve chat history",
                error={
                    "type": "server_error",
                    "description": str(e)
                }
            )
        ), 500


@chat_bp.route("/start", methods=["POST"])
def start_chat():
    """
    Start a chat session with optional voice output.

    Immediately returns a session ID.
    The transcription process is performed in a background thread,
    and status updates are streamed via the SSE endpoint.
    """
    session_id = str(uuid.uuid4())
    stop_event = Event()

    # Create status queue for this session
    status_queue = Queue()
    session_queues[session_id] = status_queue

    try:
        # Get query parameters
        mode = request.args.get("mode", "chat")
        optimize = request.args.get("optimize", "false").lower() == "true"
        chat_id = request.args.get("chat_id")
        doc_path = request.args.get("doc")

        # Validate mode
        if mode not in ["chat", "voice", "voice-save"]:
            cleanup_session(session_id)
            return jsonify(
                create_status_response(
                    "error",
                    "Invalid mode. Must be 'chat', 'voice', or 'voice-save'",
                    error={
                        "type": "invalid_parameter",
                        "description": "Invalid mode parameter",
                    },
                )
            ), 400

        # Initialize handlers
        chat_handler = ChatHandler()
        recorder = AudioRecorder()
        transcriber = WhisperTranscriber()

        # Handle document path
        if doc_path:
            if not validate_file_path(Path(doc_path)):
                cleanup_session(session_id)
                return jsonify(
                    create_status_response(
                        "error",
                        "Invalid document path",
                        error={
                            "type": "invalid_parameter",
                            "description": "Invalid document path provided",
                        },
                    )
                ), 400

        # Handle existing chat
        if chat_id:
            if not chat_handler.load_existing_chat(chat_id):
                cleanup_session(session_id)
                return jsonify(
                    create_status_response(
                        "error",
                        f"Failed to load chat session: {chat_id}",
                        error={
                            "type": "chat_error",
                            "description": "Chat session not found",
                        },
                    )
                ), 404
        else:
            chat_handler.start_new_chat(doc_path=doc_path)

        # Create status callback to queue SSE events
        status_callback = create_status_callback(session_id, status_queue)

        # Configure chat parameters
        use_kokoro = mode in ["voice", "voice-save"]
        save_to_file = mode == "voice-save"
        stream_to_speakers = mode in ["voice", "voice-save"]

        # Start the transcription process in a background thread.
        def background_transcription():
            with recorder:
                success, error_message, response_data = handle_transcription(
                    recorder,
                    transcriber,
                    copy_to_clipboard=False,
                    output_file=None,
                    use_kokoro=use_kokoro,
                    use_llm=True,
                    chat_handler=chat_handler,
                    stream_to_speakers=stream_to_speakers,
                    save_to_file=save_to_file,
                    optimize_voice=optimize,
                    status_callback=status_callback,
                    stop_event=stop_event,
                )
                if not success and error_message:
                    logging.error(
                        f"Transcription error in background task: {error_message}"
                    )

        Thread(target=background_transcription, daemon=True).start()

        # Immediately return the session ID.
        return jsonify(
            create_status_response(
                "success",
                "Chat session started",
                data={
                    "session_id": session_id,
                    "chat_id": chat_handler.chat_history.current_chat_id,
                },
            )
        ), 200

    except Exception as e:
        logging.error(f"Error starting chat session: {str(e)}")
        cleanup_session(session_id)
        return jsonify(
            create_status_response(
                "error",
                "Internal server error",
                error={"type": "server_error", "description": str(e)},
            )
        ), 500