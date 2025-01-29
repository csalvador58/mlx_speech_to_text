# File: src/speech_to_text/llm/__init__.py
"""
LLM package for processing transcribed text.
Provides functionality for sending transcribed text to LLM and handling responses.
"""

from .mlxw_to_llm import MLXWToLLM

__all__ = ["MLXWToLLM"]