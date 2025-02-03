# File: src/speech_to_text/transcriber/whisper.py
"""
Whisper model integration for speech-to-text transcription.
Handles transcription of audio data using the MLX Whisper model.
"""

import logging
import mlx.core as mx
from typing import Optional, Dict, Any, Tuple
from mlx_whisper.transcribe import transcribe
from speech_to_text.config.settings import (
    MODEL_NAME,
    VERBOSE,
    WORD_TIMESTAMPS,
    MINIMUM_WORD_COUNT,
    SUSPICIOUS_RESPONSES,
)


class WhisperTranscriber:
    """Handles transcription of audio using the MLX Whisper model."""

    def __init__(self, model_name: str = MODEL_NAME):
        """
        Initialize the WhisperTranscriber.

        Args:
            model_name: Name or path of the Whisper model to use
        """
        self.model_name = model_name
        logging.info(f"Initialized WhisperTranscriber with model: {model_name}")

    def transcribe_audio(
        self,
        audio_data: mx.array,
        normalize_text: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Transcribe audio data using the Whisper model.

        Args:
            audio_data: Normalized audio data as mlx array
            normalize_text: Whether to normalize the transcribed text

        Returns:
            Optional[Dict[str, Any]]: Dictionary containing transcription results or None if failed
        """

        if audio_data is None or len(audio_data) == 0:
            logging.error("No audio data provided for transcription")
            return None

        try:
            # Ensure audio_data is in float32 format (MLX-Whisper expects normalized input)
            audio_data = audio_data.astype(mx.float32)

            logging.info("Starting transcription...")
            # Perform transcription using MLX Whisper
            result = transcribe(
                audio_data,
                path_or_hf_repo=self.model_name,
                verbose=VERBOSE,
                word_timestamps=WORD_TIMESTAMPS,
            )

            if normalize_text:
                result["text"] = self._normalize_text(result["text"])

            logging.info("Transcription completed, validating result...")
            is_valid, error_message = self.validate_transcription(result["text"])
            if not is_valid:
                logging.error(f"Transcription validation failed: {error_message}")
                result["validation_error"] = error_message

            return result

        except Exception as e:
            logging.error(f"Error during transcription: {e}")
            return None

    def _normalize_text(self, text: str) -> str:
        """
        Normalize transcribed text.

        Args:
            text: Raw transcribed text

        Returns:
            str: Normalized text
        """
        if not text:
            return ""

        # Strip whitespace and convert to lowercase
        normalized = text.strip().lower()
        return normalized

    def validate_transcription(self, text: str) -> Tuple[bool, Optional[str]]:
        """
        Validate transcription quality based on content and length.

        Args:
            text: Transcribed text to validate

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message if invalid)
        """
        if not text:
            return False, "Empty transcription"

        normalized_text = self._normalize_text(text)

        # Check word count
        word_count = len(normalized_text.split())
        if word_count < MINIMUM_WORD_COUNT:
            return (
                False,
                f"Transcription too short ({word_count} words) - possible audio quality issue",
            )

        # Check for suspicious responses
        if normalized_text in [self._normalize_text(r) for r in SUSPICIOUS_RESPONSES]:
            return False, "Low confidence transcription detected"

        return True, None

    def check_exit_command(self, transcription: Dict[str, Any]) -> bool:
        """
        Check if the transcription contains an exit command.

        Args:
            transcription: Transcription result dictionary

        Returns:
            bool: True if exit command detected, False otherwise
        """
        if not transcription or "text" not in transcription:
            return False

        text = transcription["text"].strip().lower()
        return text == "exit"

    def get_transcribed_text(self, transcription: Dict[str, Any]) -> Optional[str]:
        """
        Extract the transcribed text from the transcription result.

        Args:
            transcription: Transcription result dictionary

        Returns:
            Optional[str]: Transcribed text or None if not available
        """
        if not transcription or "text" not in transcription:
            return None

        return transcription["text"]
