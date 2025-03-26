# File: src/speech_to_text/llm/__init__.py
"""
LLM module for speech-to-text application.
Provides LLM integration and file processing capabilities.
"""

from .mlxw_to_llm import MLXWToLLM
from .file_handler import process_file, prepare_content_message

__all__ = ['MLXWToLLM', 'process_file', 'prepare_content_message']