# File: src/speech_to_text/api/connect.py

from flask import Blueprint, request, jsonify
import logging
from speech_to_text.audio.recorder import AudioRecorder
from speech_to_text.transcriber.whisper import WhisperTranscriber
from speech_to_text.utils import handle_transcription
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

@connect_bp.route("/chat", methods=["POST"])
def speech_to_chat():
    """
    Handle speech-to-chat requests.
    Expects JSON data with speech content and optional chat parameters.
    """
    if not request.is_json:
        return jsonify({
            "status": "error",
            "message": "Content-Type must be application/json"
        }), 400
    
    try:
        data = request.json
        
        # Validate required fields
        if "content" not in data:
            return jsonify({
                "status": "error",
                "message": "Missing required field: content"
            }), 400
            
        # Optional chat parameters
        chat_id = data.get("chat_id")
        
        # TODO: Implement speech-to-chat logic
        # For now, just acknowledge receipt
        return jsonify({
            "status": "success",
            "message": "Chat content received",
            "data": {
                "content": data["content"],
                "chat_id": chat_id
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Error processing speech-to-chat request: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500