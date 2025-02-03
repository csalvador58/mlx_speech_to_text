# File: src/speech_to_text/utils/transcription_utils.py
"""
Utility functions for handling transcription operations.
Provides reusable functions for saving and processing transcriptions.
"""

import logging
import time
from typing import Optional, Tuple, Callable, Dict, Any
from threading import Event

from speech_to_text.audio.recorder import AudioRecorder
from speech_to_text.transcriber.whisper import WhisperTranscriber
from speech_to_text.chat import ChatHandler
from speech_to_text.llm import MLXWToLLM
from speech_to_text.kokoro import KokoroHandler
from speech_to_text.utils.path_utils import safe_write_file

def save_transcription(text: str, output_file: Optional[str]) -> None:
    """
    Save transcription to a file.
    
    Args:
        text: Text content to save
        output_file: File path to save to. If None or empty, no save is performed.
    """
    if not text or not output_file:
        return
        
    if safe_write_file(text, output_file):
        logging.info(f"Transcription saved to: {output_file}")
    else:
        logging.error(f"Failed to save transcription to: {output_file}")

def handle_transcription(
    recorder: AudioRecorder,
    transcriber: WhisperTranscriber,
    copy_to_clipboard: bool = False,
    output_file: Optional[str] = None,
    use_kokoro: bool = False,
    use_llm: bool = False,
    chat_handler: Optional[ChatHandler] = None,
    stream_to_speakers: bool = False,
    save_to_file: bool = True,
    optimize_voice: bool = False,
    status_callback: Optional[Callable[[str, str, Optional[int]], None]] = None,
    stop_event: Optional[Event] = None,
) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
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
        save_to_file: Whether to save audio responses to file
        optimize_voice: Whether to apply voice optimization to the text
        status_callback: Optional callback for status updates
        stop_event: Optional event to signal stopping
        
    Returns:
        Tuple[bool, Optional[str], Optional[Dict]]: (continue_flag, error_message, response_data)
    """
    def update_status(status: str, message: str, progress: Optional[int] = None):
        """Helper to call status callback if provided."""
        if status_callback:
            status_callback(status, message, progress)

    # Set status callback for recorder
    recorder.set_status_callback(status_callback)
    
    # Start calibration
    recorder.calibrate_silence_threshold()
    
    # Check if we should stop
    if stop_event and stop_event.is_set():
        return False, "Recording stopped", None

    # Record audio
    frames, success = recorder.record_audio()
    if not success or not frames:
        error_msg = "Failed to record audio"
        logging.error(error_msg)
        update_status("error", error_msg, None)
        return True, error_msg, None

    # Process audio frames
    audio_data = recorder.process_audio_frames(frames)
    if audio_data is None:
        error_msg = "Failed to process audio frames"
        logging.error(error_msg)
        update_status("error", error_msg, None)
        return True, error_msg, None

    # Start transcription processing
    update_status("processing", "Processing your request...", None)
    
    # Perform transcription
    start_time = time.time()
    result = transcriber.transcribe_audio(audio_data)
    
    if result is None:
        error_msg = "Transcription failed"
        logging.error(error_msg)
        update_status("error", error_msg, None)
        return True, error_msg, None

    # Check validation error
    if "validation_error" in result:
        error_msg = result["validation_error"]
        logging.error(f"Validation error: {error_msg}")
        update_status("error", error_msg, None)
        return True, error_msg, None

    # Get transcribed text
    text = transcriber.get_transcribed_text(result)
    if not text:
        error_msg = "No text transcribed"
        logging.info(error_msg)
        update_status("error", error_msg, None)
        return True, error_msg, None

    logging.info(f"Transcription: {text}")

    response_data = {"transcription": text}

    # Handle chat mode
    if chat_handler:
        continue_chat, response = chat_handler.process_message(
            text,
            use_kokoro=use_kokoro,
            stream_to_speakers=stream_to_speakers,
            save_to_file=save_to_file,
            optimize_voice=optimize_voice
        )
        
        if stream_to_speakers:
            update_status("streaming", "Playing response audio...", None)
            
        if response:
            response_data["chat_response"] = response
            chat_id = chat_handler.chat_history.current_chat_id
            update_status("complete", response, None)
            response_data["chat_id"] = chat_id
            
        return continue_chat, None, response_data

    # Handle clipboard copy
    if copy_to_clipboard:
        try:
            import pyperclip
            pyperclip.copy(text)
            logging.info("Text copied to clipboard")
            update_status("complete", "Ready to paste from clipboard", None)
        except Exception as e:
            error_msg = f"Failed to copy to clipboard: {e}"
            logging.error(error_msg)
            update_status("error", error_msg, None)
            return True, error_msg, response_data

    # Handle file output
    files_saved = []
    if output_file:
        save_transcription(text, output_file)
        files_saved.append(output_file)

    # Check for exit command
    if transcriber.check_exit_command(result):
        logging.info("Exit command received")
        return False, None, response_data

    # Handle LLM processing
    if use_llm:
        try:
            llm_handler = MLXWToLLM()
            llm_response = llm_handler.process_text(text)
            if llm_response:
                logging.info("LLM processing completed successfully")
                response_data["llm_response"] = llm_response
                if output_file:
                    save_transcription(llm_response, output_file)
                    files_saved.append(output_file)
                update_status("complete", llm_response, None)
        except Exception as e:
            error_msg = f"Error in LLM processing: {e}"
            logging.error(error_msg)
            update_status("error", error_msg, None)
            return True, error_msg, response_data

    # Handle Kokoro conversion
    if use_kokoro and not stream_to_speakers:  # Skip if already streaming
        try:
            kokoro_handler = KokoroHandler()
            output_path = kokoro_handler.convert_text_to_speech(
                text,
                optimize=optimize_voice
            )
            if output_path:
                logging.info(f"Text-to-speech conversion saved to: {output_path}")
                response_data["audio_path"] = str(output_path)
                files_saved.append(str(output_path))
        except Exception as e:
            error_msg = f"Error in Kokoro conversion: {e}"
            logging.error(error_msg)
            update_status("error", error_msg, None)
            return True, error_msg, response_data

    # Final status update for file saves
    if files_saved and not chat_handler and not copy_to_clipboard:
        paths_msg = f"Saved to: {', '.join(files_saved)}"
        update_status("complete", paths_msg, None)

    return True, None, response_data