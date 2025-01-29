# File: src/speech_to_text/kokoro/__init__.py
"""
Kokoro package for text-to-speech conversion.
Exposes the KokoroHandler class and text optimization utilities.
"""

from .mlxw_to_kokoro import (
    KokoroHandler,
    optimize_for_voice,
)

__all__ = [
    'KokoroHandler',
    'optimize_for_voice',
]