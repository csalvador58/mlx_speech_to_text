# File: src/speech_to_text/__init__.py
"""
Speech to Text Application

A real-time speech-to-text transcription tool using MLX Whisper.
"""

__version__ = "0.1.0"

from speech_to_text.audio.recorder import AudioRecorder
from speech_to_text.transcriber.whisper import WhisperTranscriber

__all__ = [
    "AudioRecorder",
    "WhisperTranscriber",
]







