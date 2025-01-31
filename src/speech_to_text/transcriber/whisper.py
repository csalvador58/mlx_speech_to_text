# File: src/speech_to_text/transcriber/whisper.py
"""
Whisper model integration for speech-to-text transcription.
Handles transcription of audio data using the MLX Whisper model.
"""

import logging
import mlx.core as mx
from typing import Optional, Dict, Any
from mlx_whisper.transcribe import transcribe
from speech_to_text.config.settings import (
    MODEL_NAME,
    VERBOSE,
    WORD_TIMESTAMPS,
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
            
            # Perform transcription using MLX Whisper
            result = transcribe(
                audio_data,
                path_or_hf_repo=self.model_name,
                verbose=VERBOSE,
                word_timestamps=WORD_TIMESTAMPS,
            )

            if normalize_text:
                result["text"] = self._normalize_text(result["text"])
                
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