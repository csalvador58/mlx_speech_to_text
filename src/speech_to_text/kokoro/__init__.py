# File: src/speech_to_text/kokoro/__init__.py
"""
Kokoro package for text-to-speech conversion.
Provides functionality for converting transcribed text to speech using the Kokoro API.
"""

from .mlxw_to_kokoro import KokoroHandler

__all__ = ["KokoroHandler"]