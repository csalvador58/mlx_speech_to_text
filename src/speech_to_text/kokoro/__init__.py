# File: src/speech_to_text/kokoro/__init__.py
"""
Kokoro package for text-to-speech conversion.
Exposes the KokoroHandler class for text-to-speech functionality.
"""

from .mlxw_to_kokoro import KokoroHandler

__all__ = [
    'KokoroHandler'
]