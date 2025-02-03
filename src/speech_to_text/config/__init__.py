# File: src/speech_to_text/config/__init__.py
"""
Configuration package for speech-to-text application.
Contains all configuration settings and constants.
"""

from .settings import (
    KOKORO_BASE_URL,
    KOKORO_API_KEY,
    KOKORO_MODEL,
    KOKORO_VOICE,
    KOKORO_SPEED,
    KOKORO_RESPONSE_FORMAT,
    KOKORO_OUTPUT_FILENAME,
    OUTPUT_DIR,
    MLXW_OUTPUT_FILENAME,  # From the main.py usage
)
from .text_optimizations import optimizer

__all__ = [
    # Settings exports
    "KOKORO_BASE_URL",
    "KOKORO_API_KEY",
    "KOKORO_MODEL",
    "KOKORO_VOICE",
    "KOKORO_SPEED",
    "KOKORO_RESPONSE_FORMAT",
    "KOKORO_OUTPUT_FILENAME",
    "OUTPUT_DIR",
    "MLXW_OUTPUT_FILENAME",
    # Text optimization exports
    "optimizer",
]
