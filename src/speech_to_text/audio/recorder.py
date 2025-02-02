# File: src/speech_to_text/audio/recorder.py
"""
Audio recording functionality for the speech-to-text application.
Handles microphone input and audio processing.
"""

import logging
import sys
import mlx.core as mx
import pyaudio
from typing import Optional, List, Tuple

from speech_to_text.config.settings import (
    AUDIO_FORMAT,
    CHANNELS,
    SAMPLE_RATE,
    CHUNK_SIZE,
    SILENCE_CHUNKS,
    DEFAULT_SILENCE_THRESHOLD,
    CALIBRATION_FRAMES,
    CALIBRATION_BUFFER,
)

class AudioRecorder:
    """Handles audio recording and processing from the microphone."""
    
    def __init__(self):
        """Initialize the audio recorder with PyAudio."""
        self.audio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        self.silence_threshold: float = DEFAULT_SILENCE_THRESHOLD
        
    def __enter__(self):
        """Context manager entry point."""
        return self
        
    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Context manager exit point for cleanup."""
        self.cleanup()

    def start_stream(self) -> None:
        """Start the audio input stream."""
        if self.stream is None:
            self.stream = self.audio.open(
                format=AUDIO_FORMAT,
                channels=CHANNELS,
                rate=SAMPLE_RATE,
                input=True,
                frames_per_buffer=CHUNK_SIZE
            )
            logging.info("Audio stream started")

    def stop_stream(self) -> None:
        """Stop the audio input stream."""
        if self.stream is not None:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
            logging.info("Audio stream stopped")

    def cleanup(self) -> None:
        """Clean up resources."""
        self.stop_stream()
        self.audio.terminate()
        logging.info("Audio resources cleaned up")

    def calibrate_silence_threshold(self) -> float:
        """
        Calibrate the silence threshold based on background noise.
        
        Returns:
            float: Calibrated silence threshold value
        """
        logging.info("Calibrating silence threshold...")
        self.start_stream()
        
        try:
            background_frames = []
            for _ in range(CALIBRATION_FRAMES):
                data = self.stream.read(CHUNK_SIZE, exception_on_overflow=False)
                
                # Ensure data is properly formatted
                if not data:
                    logging.warning("Empty audio data received during calibration.")
                    continue

                # Cast the memoryview to 'h' to interpret the bytes as int16 values.
                audio_data = mx.array(memoryview(data).cast('h'), dtype=mx.int16)
                max_value = mx.max(mx.abs(audio_data)).item()
                background_frames.append(max_value)
            
            if not background_frames:
                logging.error("No valid background frames captured. Using default threshold.")
                self.silence_threshold = DEFAULT_SILENCE_THRESHOLD
                return self.silence_threshold
            
            background_tensor = mx.array(background_frames)
            self.silence_threshold = mx.mean(background_tensor).item() + CALIBRATION_BUFFER
            logging.info(f"Calibrated silence threshold: {self.silence_threshold}")
            
            return self.silence_threshold
            
        except Exception as e:
            logging.error(f"Error during calibration: {e}")
            self.silence_threshold = DEFAULT_SILENCE_THRESHOLD
            return self.silence_threshold

    def record_audio(self) -> Tuple[List[mx.array], bool]:
        """
        Record audio until silence is detected.
        
        Returns:
            Tuple[List[mx.array], bool]: Tuple containing:
                - List of recorded audio frames
                - Boolean indicating if recording was successful
        """
        self.start_stream()
        frames = []
        silent_chunks = 0
        last_message_length = 0
        
        try:
            while True:
                data = self.stream.read(CHUNK_SIZE, exception_on_overflow=False)
                # Correctly cast the data to int16 using memoryview.cast('h')
                audio_data = mx.array(memoryview(data).cast('h'), dtype=mx.int16) 
                
                max_amplitude = mx.max(mx.abs(audio_data)).item()
                logging.debug(f"Detected max amplitude: {max_amplitude}, Silence threshold: {self.silence_threshold}")

                if max_amplitude < self.silence_threshold:
                    progress = silent_chunks / SILENCE_CHUNKS
                    bar_length = 30  # Length of the progress bar
                    filled_length = int(progress * bar_length)
                    bar = "#" * filled_length + "-" * (bar_length - filled_length)
                    message = f"Silence delay [{bar}]"
                    
                    sys.stdout.write(f"\r{' ' * last_message_length}\r")
                    sys.stdout.write(message)
                    sys.stdout.flush()
                    last_message_length = len(message)
                    
                    silent_chunks += 1
                else:
                    silent_chunks = 0

                if silent_chunks > SILENCE_CHUNKS:
                    break

                frames.append(audio_data)

            sys.stdout.write("\n")
            sys.stdout.flush()

            return frames, True

        except Exception as e:
            logging.error(f"Error recording audio: {e}")
            return frames, False

    def process_audio_frames(self, frames: List[mx.array]) -> Optional[mx.array]:
        """
        Process recorded audio frames into a format suitable for transcription.
        
        Args:
            frames: List of recorded audio frames (MLX arrays)
            
        Returns:
            Optional[mx.array]: Processed audio data, normalized to float32
        """
        if not frames:
            return None
            
        try:
            # Concatenate all audio frames and normalize
            audio_data = mx.concatenate(frames).astype(mx.float32) / 32768.0
            return audio_data
            
        except Exception as e:
            logging.error(f"Error processing audio frames: {e}")
            return None