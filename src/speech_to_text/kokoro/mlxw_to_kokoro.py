# File: src/speech_to_text/kokoro/mlxw_to_kokoro.py
"""
Kokoro text-to-speech integration for converting transcribed text to speech.
Handles the conversion of text to speech using the Kokoro API.
"""

import logging
import os
from typing import Optional
import pyaudio
from openai import OpenAI

from speech_to_text.config.settings import (
    KOKORO_BASE_URL,
    KOKORO_API_KEY,
    KOKORO_MODEL,
    KOKORO_VOICE,
    KOKORO_SPEED,
    KOKORO_RESPONSE_FORMAT,
    KOKORO_OUTPUT_FILENAME,
    OUTPUT_DIR,
)
from speech_to_text.config.text_optimizations import optimizer


class KokoroHandler:
    """Handles text-to-speech conversion using the Kokoro API."""

    def __init__(self):
        """Initialize the Kokoro handler with OpenAI client."""
        self.client = OpenAI(base_url=KOKORO_BASE_URL, api_key=KOKORO_API_KEY)
        self._ensure_output_directory()

    def _ensure_output_directory(self) -> None:
        """Ensure the output directory exists."""
        try:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
        except Exception as e:
            logging.error(f"Error creating output directory: {e}")
            raise

    def _save_audio_to_file(self, text: str, optimize: bool = False) -> Optional[str]:
        """
        Save audio to file using Kokoro API.

        Args:
            text: Text to convert to speech
            optimize: Whether to apply voice optimization

        Returns:
            Optional[str]: Path to saved file if successful, None otherwise
        """
        try:
            with self.client.audio.speech.with_streaming_response.create(
                model=KOKORO_MODEL,
                voice=KOKORO_VOICE,
                speed=KOKORO_SPEED,
                input=text,
                response_format=KOKORO_RESPONSE_FORMAT,
            ) as response:
                logging.debug(
                    f"Saving audio response to file - Status: {response.status_code}"
                )
                response.stream_to_file(KOKORO_OUTPUT_FILENAME)
                return KOKORO_OUTPUT_FILENAME
        except Exception as e:
            logging.error(f"Error saving audio to file: {e}")
            return None

    def convert_text_to_speech(
        self, text: str, optimize: bool = False
    ) -> Optional[str]:
        """
        Convert text to speech using Kokoro API and save to file.

        Args:
            text: Text to convert to speech
            optimize: Whether to apply voice optimization to the text

        Returns:
            Optional[str]: Path to the output audio file if successful, None otherwise
        """
        if not text:
            logging.error("No text provided for text-to-speech conversion")
            return None

        try:
            logging.debug(f"Original text: {text}")

            if optimize:
                text = optimizer(text)
                logging.debug(f"Optimized text: {text}")

            logging.debug(
                f"Making request to Kokoro API - URL: {KOKORO_BASE_URL}/audio/speech"
            )
            logging.debug(
                f"Request parameters - Model: {KOKORO_MODEL}, Voice: {KOKORO_VOICE}, Format: {KOKORO_RESPONSE_FORMAT}"
            )

            return self._save_audio_to_file(text, optimize)

        except Exception as e:
            logging.error(f"Error during text-to-speech conversion: {e}")
            return None

    def stream_text_to_speakers(
        self, text: str, optimize: bool = False, save_to_file: bool = True
    ) -> Optional[str]:
        """
        Convert text to speech and stream to speakers. Optionally save to file.

        Args:
            text: Text to convert to speech
            optimize: Whether to apply voice optimization to the text
            save_to_file: Whether to save the audio to file after streaming

        Returns:
            Optional[str]: Path to the saved audio file if saved, None otherwise
        """
        if not text:
            logging.error("No text provided for text-to-speech streaming")
            return None

        try:
            logging.debug(f"Voice text optimization is enabled: {optimize}")
            logging.debug(f"Original text: {text}")

            if optimize:
                text = optimizer(text)
                logging.debug(f"Optimized text: {text}")

            # Initialize PyAudio
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=pyaudio.paInt16, channels=1, rate=24000, output=True
            )

            logging.debug(
                f"Making streaming request to Kokoro API - URL: {KOKORO_BASE_URL}/audio/speech"
            )
            logging.debug(
                f"Request parameters - Model: {KOKORO_MODEL}, Voice: {KOKORO_VOICE}, Format: pcm"
            )

            # Stream to speakers
            with self.client.audio.speech.with_streaming_response.create(
                model=KOKORO_MODEL,
                voice=KOKORO_VOICE,
                speed=KOKORO_SPEED,
                input=text,
                response_format="pcm",  # Use PCM format for direct streaming
            ) as response:
                logging.debug(
                    f"Received streaming response - Status: {response.status_code}"
                )
                for chunk in response.iter_bytes(chunk_size=1024):
                    stream.write(chunk)

            # Clean up audio stream
            stream.stop_stream()
            stream.close()
            audio.terminate()

            logging.debug("Successfully streamed text to speakers")

            # Save to file if requested
            if save_to_file:
                logging.debug("Saving streamed audio to file...")
                return self._save_audio_to_file(text, optimize)
            return None

        except Exception as e:
            logging.error(f"Error during text-to-speech streaming: {e}")
            return None
