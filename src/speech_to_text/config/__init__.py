# File: src/speech_to_text/config/__init__.py
"""
Configuration package for speech-to-text application.
Contains all configuration settings and constants.
"""

from .settings import *
from .text_optimizations import (
    WORD_REPLACEMENTS,
    PUNCTUATION_REPLACEMENTS,
    GLOBAL_REPLACEMENTS,
)