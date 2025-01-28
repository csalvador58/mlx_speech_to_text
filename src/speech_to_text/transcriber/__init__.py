# File: src/speech_to_text/transcriber/__init__.py
"""
Transcription package for speech-to-text processing.
Handles all transcription-related functionality.
"""

from .whisper import WhisperTranscriber

__all__ = ["WhisperTranscriber"]