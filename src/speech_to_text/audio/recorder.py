# File: src/speech_to_text/audio/recorder.py
"""
Audio recording functionality for the speech-to-text application.
Handles microphone input and audio processing.
"""

import logging
import sys
import mlx.core as mx
import pyaudio
from typing import Optional, List, Tuple, Callable

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
        self._status_callback: Optional[Callable] = None
        
    def __enter__(self):
        """Context manager entry point."""
        return self
        
    def __exit__(self, exc_type, exc_value, traceback) -> None:
        """Context manager exit point for cleanup."""
        self.cleanup()

    def set_status_callback(self, callback: Callable[[str, str, Optional[int]], None]) -> None:
        """Set status callback function."""
        self._status_callback = callback

    def _emit_status(self, status: str, message: str, progress: Optional[int] = None) -> None:
        """Emit status update if callback is set."""
        if self._status_callback:
            self._status_callback(status, message, progress)

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
        """Calibrate the silence threshold based on background noise."""
        logging.info("Calibrating silence threshold...")
        self._emit_status("calibrating", "Starting background calibration...", None)
        self.start_stream()
        
        try:
            background_frames = []
            for _ in range(CALIBRATION_FRAMES):
                data = self.stream.read(CHUNK_SIZE, exception_on_overflow=False)
                if not data:
                    continue
                audio_data = mx.array(memoryview(data).cast('h'), dtype=mx.int16)
                max_value = mx.max(mx.abs(audio_data)).item()
                background_frames.append(max_value)
            
            if not background_frames:
                logging.error("No valid background frames captured")
                self.silence_threshold = DEFAULT_SILENCE_THRESHOLD
                self._emit_status("error", "Calibration failed", None)
                return self.silence_threshold
            
            background_tensor = mx.array(background_frames)
            self.silence_threshold = mx.mean(background_tensor).item() + CALIBRATION_BUFFER
            logging.info(f"Calibrated silence threshold: {self.silence_threshold}")
            return self.silence_threshold
            
        except Exception as e:
            logging.error(f"Error during calibration: {e}")
            self.silence_threshold = DEFAULT_SILENCE_THRESHOLD
            self._emit_status("error", f"Calibration error: {str(e)}", None)
            return self.silence_threshold

    def record_audio(self) -> Tuple[List[mx.array], bool]:
        """Record audio until silence is detected."""
        self.start_stream()
        frames = []
        silent_chunks = 0
        last_message_length = 0
        recording_started = False
        
        try:
            self._emit_status("recording", "Ready for speech...", None)
            
            while True:
                data = self.stream.read(CHUNK_SIZE, exception_on_overflow=False)
                audio_data = mx.array(memoryview(data).cast('h'), dtype=mx.int16) 
                
                max_amplitude = mx.max(mx.abs(audio_data)).item()
                
                if max_amplitude < self.silence_threshold:
                    # Calculate silence progress percentage
                    progress = int((silent_chunks / SILENCE_CHUNKS) * 100)
                    
                    # Update CLI progress bar
                    bar_length = 30
                    filled_length = int((progress / 100) * bar_length)
                    bar = "#" * filled_length + "-" * (bar_length - filled_length)
                    message = f"Silence delay [{bar}]"
                    
                    sys.stdout.write(f"\r{' ' * last_message_length}\r")
                    sys.stdout.write(message)
                    sys.stdout.flush()
                    last_message_length = len(message)
                    
                    # Emit silence progress
                    self._emit_status("silence", "Detecting silence...", progress)
                    silent_chunks += 1
                else:
                    if not recording_started:
                        recording_started = True
                    silent_chunks = 0

                if silent_chunks > SILENCE_CHUNKS:
                    break

                frames.append(audio_data)

            sys.stdout.write("\n")
            sys.stdout.flush()
            return frames, True

        except Exception as e:
            logging.error(f"Error recording audio: {e}")
            self._emit_status("error", f"Recording error: {str(e)}", None)
            return frames, False

    def process_audio_frames(self, frames: List[mx.array]) -> Optional[mx.array]:
        """Process recorded audio frames for transcription."""
        if not frames:
            return None
            
        try:
            audio_data = mx.concatenate(frames).astype(mx.float32) / 32768.0
            return audio_data
            
        except Exception as e:
            logging.error(f"Error processing audio frames: {e}")
            self._emit_status("error", f"Processing error: {str(e)}", None)
            return None