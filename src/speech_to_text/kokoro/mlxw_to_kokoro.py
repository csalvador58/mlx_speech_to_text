# File: src/speech_to_text/kokoro/mlxw_to_kokoro.py
"""
Kokoro text-to-speech integration for converting transcribed text to speech.
Handles the conversion of text to speech using the Kokoro API.
"""

import logging
import os
from typing import Optional
from openai import OpenAI

from speech_to_text.config.settings import (
    KOKORO_BASE_URL,
    KOKORO_API_KEY,
    KOKORO_MODEL,
    KOKORO_VOICE,
    KOKORO_RESPONSE_FORMAT,
    KOKORO_OUTPUT_FILENAME,
    OUTPUT_DIR,
)

class KokoroHandler:
    """Handles text-to-speech conversion using the Kokoro API."""
    
    def __init__(self):
        """Initialize the Kokoro handler with OpenAI client."""
        self.client = OpenAI(
            base_url=KOKORO_BASE_URL,
            api_key=KOKORO_API_KEY
        )
        self._ensure_output_directory()
        
    def _ensure_output_directory(self) -> None:
        """Ensure the output directory exists."""
        try:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
        except Exception as e:
            logging.error(f"Error creating output directory: {e}")
            raise

    def convert_text_to_speech(self, text: str) -> Optional[str]:
        """
        Convert text to speech using Kokoro API.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Optional[str]: Path to the output audio file if successful, None otherwise
        """
        if not text:
            logging.error("No text provided for text-to-speech conversion")
            return None
            
        try:
            # Log request before making the API call
            logging.debug(f"Making request to Kokoro API - URL: {KOKORO_BASE_URL}/audio/speech")
            logging.debug(f"Request parameters - Model: {KOKORO_MODEL}, Voice: {KOKORO_VOICE}, Format: {KOKORO_RESPONSE_FORMAT}")
            
            with self.client.audio.speech.with_streaming_response.create(
                model=KOKORO_MODEL,
                voice=KOKORO_VOICE,
                input=text,
                response_format=KOKORO_RESPONSE_FORMAT
            ) as response:
                # Log successful response
                logging.debug(f"Received response from Kokoro API - Status: {response.status_code}")
                response.stream_to_file(KOKORO_OUTPUT_FILENAME)
                
            return KOKORO_OUTPUT_FILENAME
            
        except Exception as e:
            logging.error(f"Error during text-to-speech conversion: {e}")
            return None