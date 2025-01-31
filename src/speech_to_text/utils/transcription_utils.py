# File: src/speech_to_text/utils/transcription_utils.py
"""
Utility functions for handling transcription operations.
Provides reusable functions for saving and processing transcriptions.
"""

import logging
import os
import numpy as np
import time
import mlx.core as mx
from typing import Optional, Dict, Any, Tuple, List

from speech_to_text.audio.recorder import AudioRecorder
from speech_to_text.transcriber.whisper import WhisperTranscriber
from speech_to_text.chat import ChatHandler
from speech_to_text.llm import MLXWToLLM
from speech_to_text.kokoro import KokoroHandler

def save_transcription(text: str, output_file: str | None) -> None:
    """
    Save transcription to a file.
    
    Args:
        text: Text content to save
        output_file: File path to save to. If None or empty, no save is performed.
    """
    if not output_file:
        return
        
    try:
        # Ensure output directory exists
        directory = os.path.dirname(output_file)
        if directory:
            os.makedirs(directory, exist_ok=True)
        
        with open(output_file, 'w') as f:
            f.write(text)
        logging.info(f"Transcription saved to: {output_file}")
    except Exception as e:
        logging.error(f"Error saving transcription to file: {e}")
        logging.debug(f"Output file path: {output_file}")
        if directory:
            logging.debug(f"Directory exists: {os.path.exists(directory)}")
            logging.debug(f"Directory is writable: {os.access(directory, os.W_OK)}")

def handle_transcription(
    recorder: AudioRecorder,
    transcriber: WhisperTranscriber,
    copy_to_clipboard: bool = False,
    output_file: str = None,
    use_kokoro: bool = False,
    use_llm: bool = False,
    chat_handler: Optional[ChatHandler] = None,
    stream_to_speakers: bool = False,
    optimize_voice: bool = False
) -> bool:
    """
    Handle a single transcription cycle.
    
    Args:
        recorder: Audio recorder instance
        transcriber: Whisper transcriber instance
        copy_to_clipboard: Whether to copy transcription to clipboard
        output_file: File to save transcription to
        use_kokoro: Whether to convert transcription to speech using Kokoro
        use_llm: Whether to process transcription with LLM
        chat_handler: Optional chat handler for chat mode
        stream_to_speakers: Whether to stream chat responses to speakers
        optimize_voice: Whether to apply voice optimization to the text
        
    Returns:
        bool: False if exit command detected, True otherwise
    """
    # Record audio
    frames, success = recorder.record_audio()
    if not success or not frames:
        logging.error("Failed to record audio")
        return True

    # Process audio frames
    audio_data = recorder.process_audio_frames(frames)
    if audio_data is None:
        logging.error("Failed to process audio frames")
        return True

    # Perform transcription
    def generate_large_audio_data(duration_sec: int = 60, sample_rate: int = 16000) -> np.ndarray:
        """
        Generate a large NumPy array simulating audio data.

        Args:
            duration_sec: Length of the audio in seconds.
            sample_rate: Sampling rate (default 16kHz for Whisper).

        Returns:
            A NumPy array simulating raw PCM audio.
        """
        total_samples = duration_sec * sample_rate  # Total number of samples

        simulated_audio = np.random.randint(
            -32768, 32767, total_samples, dtype=np.int16
        )  # Simulating real PCM audio

        # Normalize to float32 range (-1 to 1), as Whisper expects normalized audio
        normalized_audio = simulated_audio.astype(np.float32) / 32768.0

        return normalized_audio


    # Example: Generate 5 minutes (300 seconds) of synthetic audio
    large_audio_data_np = generate_large_audio_data(duration_sec=300, sample_rate=16000)
    print(f"Generated synthetic audio data of shape: {large_audio_data_np.shape}")

    # Convert to an MLX array with MLX dtype
    large_audio_data_mx = mx.array(large_audio_data_np)
    
    # Start timing
    print("Start timer")
    start_time = time.time()

    result = transcriber.transcribe_audio(large_audio_data_mx)

    # End timing and print duration
    end_time = time.time()
    execution_time = end_time - start_time
    logging.debug(f"transcribe_audio completed in {execution_time:.6f} seconds")

    if result:
        print("Transcription successful!")
        print(result["text"][:500])  # Print first 500 characters
    else:
        print("Transcription failed!")

    
    result = transcriber.transcribe_audio(audio_data)
    if result is None:
        logging.error("Transcription failed")
        return True

    # Get transcribed text
    text = transcriber.get_transcribed_text(result)
    if not text:
        logging.info("No text transcribed")
        return True

    logging.info(f"Transcription: {text}")

    # Handle chat mode
    if chat_handler:
        continue_chat, response = chat_handler.process_message(
            text,
            use_kokoro=use_kokoro,
            stream_to_speakers=stream_to_speakers,
            optimize_voice=optimize_voice  # Pass the optimize flag to chat handler
        )
        if response:
            logging.info(f"Chat response: {response}")
        return continue_chat

    # Handle clipboard copy
    if copy_to_clipboard:
        try:
            import pyperclip
            pyperclip.copy(text)
            logging.info("Text copied to clipboard")
        except Exception as e:
            logging.error(f"Failed to copy to clipboard: {e}")

    # Handle file output
    if output_file:
        save_transcription(text, output_file)

    # Check for exit command
    if transcriber.check_exit_command(result):
        logging.info("Exit command received")
        return False

    # Handle LLM processing
    if use_llm:
        try:
            llm_handler = MLXWToLLM()
            llm_response = llm_handler.process_text(text)
            if llm_response:
                logging.info("LLM processing completed successfully")
                save_transcription(llm_response, output_file)
        except Exception as e:
            logging.error(f"Error in LLM processing: {e}")

    # Handle Kokoro conversion
    if use_kokoro:
        try:
            kokoro_handler = KokoroHandler()
            output_path = kokoro_handler.convert_text_to_speech(
                text,
                optimize=optimize_voice  # Pass the optimize flag
            )
            if output_path:
                logging.info(f"Text-to-speech conversion saved to: {output_path}")
        except Exception as e:
            logging.error(f"Error in Kokoro conversion: {e}")

    return True