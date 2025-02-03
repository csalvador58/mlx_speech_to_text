# File: src/speech_to_text/__init__.py
"""
Speech to Text Application API

A Flask-based REST API for real-time speech-to-text transcription using MLX Whisper.
Provides endpoints for transcription, chat integration, and clipboard operations.
"""

__version__ = "0.1.0"

from flask import Flask
from flask_cors import CORS
from speech_to_text.audio.recorder import AudioRecorder
from speech_to_text.transcriber.whisper import WhisperTranscriber

__all__ = ["AudioRecorder", "WhisperTranscriber", "create_app"]


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Enable CORS
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": ["http://127.0.0.1:8081"],
                "methods": ["GET", "POST", "OPTIONS"],
                "allow_headers": ["Content-Type"],
            }
        },
    )

    # Register the API blueprint
    from .api.connect import connect_bp

    app.register_blueprint(connect_bp, url_prefix="/api/connect")

    return app
