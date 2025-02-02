# File: src/speech_to_text/api/connect.py

from flask import Blueprint, request, jsonify
import logging
from pathlib import Path
from speech_to_text.audio.recorder import AudioRecorder
from speech_to_text.transcriber.whisper import WhisperTranscriber
from speech_to_text.utils import handle_transcription
from speech_to_text.chat import ChatHandler
from speech_to_text.utils.path_utils import validate_file_path
import pyperclip

connect_bp = Blueprint("connect", __name__)

@connect_bp.route("/copy/start", methods=["POST"])
def start_recording():
    """
    Start recording audio for transcription and clipboard copy.
    No input data required - simply triggers the recording process.
    """
    try:
        recorder = AudioRecorder()
        transcriber = WhisperTranscriber()
        
        # Start recording process
        with recorder:
            # Calibrate silence threshold
            recorder.calibrate_silence_threshold()
            
            # Handle the transcription
            success = handle_transcription(
                recorder,
                transcriber,
                copy_to_clipboard=True,
                output_file=None,
                use_kokoro=False,
                use_llm=False,
                chat_handler=None,
                stream_to_speakers=False,
                save_to_file=False,
                optimize_voice=False
            )
            
            if success:
                # Get the clipboard content to verify and return
                clipboard_content = pyperclip.paste()
                return jsonify({
                    "status": "success",
                    "message": "Audio recorded and transcribed",
                    "data": {
                        "transcription": clipboard_content
                    }
                }), 200
            else:
                return jsonify({
                    "status": "error",
                    "message": "Failed to process audio"
                }), 500
                
    except Exception as e:
        logging.error(f"Error in speech recording process: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Internal server error",
            "error": str(e)
        }), 500

@connect_bp.route("/chat/start", methods=["POST"])
def start_chat():
    """
    Start a chat session with optional voice output.
    Query Parameters:
    - mode: 'chat' | 'voice' | 'voice-save'
    - optimize: boolean (optional)
    - chat_id: string (optional)
    - doc: string (optional)
    """
    try:
        # Get query parameters
        mode = request.args.get('mode', 'chat')
        optimize = request.args.get('optimize', 'false').lower() == 'true'
        chat_id = request.args.get('chat_id')
        doc_path = request.args.get('doc')
        
        # Validate mode
        if mode not in ['chat', 'voice', 'voice-save']:
            return jsonify({
                "status": "error",
                "message": "Invalid mode. Must be 'chat', 'voice', or 'voice-save'"
            }), 400

        # Initialize chat handler
        chat_handler = ChatHandler()

        # Handle document path if provided
        if doc_path:
            if not validate_file_path(Path(doc_path)):
                return jsonify({
                    "status": "error",
                    "message": "Invalid document path"
                }), 400

        # Handle existing chat if chat_id provided
        if chat_id:
            if not chat_handler.load_existing_chat(chat_id):
                return jsonify({
                    "status": "error",
                    "message": f"Failed to load chat session: {chat_id}"
                }), 404
        else:
            chat_handler.start_new_chat(doc_path=doc_path)

        # Initialize recorder and transcriber
        recorder = AudioRecorder()
        transcriber = WhisperTranscriber()

        # Configure chat parameters based on mode
        use_kokoro = mode in ['voice', 'voice-save']
        save_to_file = mode == 'voice-save'
        stream_to_speakers = mode in ['voice', 'voice-save']

        # Start recording process
        with recorder:
            recorder.calibrate_silence_threshold()
            
            success = handle_transcription(
                recorder,
                transcriber,
                copy_to_clipboard=False,
                output_file=None,
                use_kokoro=use_kokoro,
                use_llm=True,
                chat_handler=chat_handler,
                stream_to_speakers=stream_to_speakers,
                save_to_file=save_to_file,
                optimize_voice=optimize
            )

            if success:
                return jsonify({
                    "status": "success",
                    "message": "Chat session started",
                    "data": {
                        "chat_id": chat_handler.chat_history.current_chat_id,
                        "mode": mode,
                        "optimize": optimize
                    }
                }), 200
            else:
                return jsonify({
                    "status": "error",
                    "message": "Failed to process audio"
                }), 500

    except Exception as e:
        logging.error(f"Error starting chat session: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Internal server error",
            "error": str(e)
        }), 500