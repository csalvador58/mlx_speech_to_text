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
    Start a chat session with optional voice output and document context.

    Query Parameters:
        mode (str): Type of chat interaction
            - 'chat': Regular text chat
            - 'voice': Voice response streamed to speakers
            - 'voice-save': Voice response saved to file
        optimize (bool): Enable voice optimization (default: false)
        chat_id (str, optional): Resume existing chat session
        doc (str, optional): Path to document for analysis
            - Can be used with new or existing chat sessions
            - Document context is applied per request
            - Does not modify chat history

    Returns:
        JSON Response:
        {
            "status": "success",
            "message": "Chat session started",
            "data": {
                "session_id": "uuid-string",
                "chat_id": "chat-uuid-string",
                "doc_path": "/path/to/doc.txt"  # If document provided
            }
        }
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

        # Create response data structure
        response_data = {
            "session_id": session_id,
        }

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

        # Handle document path validation
        validated_doc_path = None
        if doc_path:
            validated_doc_path = validate_file_path(Path(doc_path), must_exist=True)
            if not validated_doc_path:
                cleanup_session(session_id)
                return jsonify(
                    create_status_response(
                        "error",
                        "Invalid document path or file not found",
                        error={
                            "type": "invalid_parameter",
                            "description": "Invalid or inaccessible document path provided",
                        },
                    )
                ), 400
            response_data["doc_path"] = str(validated_doc_path)
            logging.info(f"Using document context from: {validated_doc_path}")

        # Handle chat session initialization
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
            response_data["chat_id"] = chat_id
            logging.info(f"Resumed existing chat session: {chat_id}")
        else:
            chat_handler.start_new_chat()
            response_data["chat_id"] = chat_handler.chat_history.current_chat_id
            logging.info("Started new chat session")

        # Create status callback to queue SSE events
        status_callback = create_status_callback(session_id, status_queue)

        # Configure chat parameters
        use_kokoro = mode in ["voice", "voice-save"]
        save_to_file = mode == "voice-save"
        stream_to_speakers = mode in ["voice", "voice-save"]

        # Start the transcription process in a background thread
        def background_transcription():
            try:
                with recorder:
                    # Update status with document context if present
                    if validated_doc_path:
                        status_callback(
                            "processing",
                            f"Loading document context: {validated_doc_path.name}",
                            None
                        )

                    success, error_message, process_response = handle_transcription(
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
                        doc_path=str(validated_doc_path) if validated_doc_path else None,
                        status_callback=status_callback,
                        stop_event=stop_event,
                    )

                    if not success and error_message:
                        logging.error(
                            f"Transcription error in background task: {error_message}"
                        )

            except Exception as e:
                error_msg = f"Error in background transcription: {str(e)}"
                logging.error(error_msg)
                status_callback("error", error_msg, None)

        Thread(target=background_transcription, daemon=True).start()

        # Return session information immediately
        return jsonify(
            create_status_response(
                "success",
                "Chat session started",
                data=response_data
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