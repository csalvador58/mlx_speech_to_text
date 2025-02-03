# File: src/speech_to_text/api/connect_copy.py

import logging
import uuid
from flask import Blueprint, jsonify
from queue import Queue
from threading import Event

from speech_to_text.audio.recorder import AudioRecorder
from speech_to_text.transcriber.whisper import WhisperTranscriber
from speech_to_text.utils import handle_transcription
from speech_to_text.utils.api_utils import (
    create_status_response,
    create_status_callback,
    session_queues,
    cleanup_session
)
import pyperclip

copy_bp = Blueprint("connect_copy", __name__)

@copy_bp.route("/start", methods=["POST"])
def start_recording():
    """Start recording audio for transcription and clipboard copy."""
    session_id = str(uuid.uuid4())
    stop_event = Event()
    
    # Create status queue for this session
    status_queue = Queue()
    session_queues[session_id] = status_queue
    
    try:
        # Initialize handlers
        recorder = AudioRecorder()
        transcriber = WhisperTranscriber()
        
        # Create status callback
        status_callback = create_status_callback(session_id, status_queue)
        
        # Start recording process
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
                stop_event=stop_event
            )
            
            if success and not error_message and response_data:
                # Get the clipboard content to verify
                clipboard_content = pyperclip.paste()
                return jsonify(create_status_response(
                    "success",
                    "Audio processed and copied to clipboard",
                    data={
                        "transcription": clipboard_content,
                        "session_id": session_id
                    }
                )), 200
            else:
                cleanup_session(session_id)
                return jsonify(create_status_response(
                    "error",
                    error_message or "Failed to process audio",
                    error={
                        "type": "transcription_error",
                        "description": error_message or "Unknown error occurred"
                    }
                )), 422
                
    except Exception as e:
        logging.error(f"Error in speech recording process: {str(e)}")
        cleanup_session(session_id)
        return jsonify(create_status_response(
            "error",
            "Internal server error",
            error={
                "type": "server_error",
                "description": str(e)
            }
        )), 500