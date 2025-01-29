# File: src/main.py
"""
Main entry point for the speech-to-text application.
Handles command line arguments and orchestrates the transcription process.
"""

import argparse
import logging
import os
import pyperclip
from pathlib import Path

from speech_to_text.audio.recorder import AudioRecorder
from speech_to_text.transcriber.whisper import WhisperTranscriber
from speech_to_text.utils.logging import setup_logging
from speech_to_text.kokoro import KokoroHandler
from speech_to_text.llm import MLXWToLLM
from speech_to_text.config.settings import (
    MLXW_OUTPUT_FILENAME,
    OUTPUT_DIR,
    LLM_OUTPUT_FILENAME,
    KOKORO_OUTPUT_FILENAME
)

def verify_output_directory() -> None:
    """Verify and create output directory if it doesn't exist."""
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        logging.info(f"Output directory verified/created: {OUTPUT_DIR}")
        
        # Test write permissions
        test_file = os.path.join(OUTPUT_DIR, 'test_write.txt')
        try:
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
            logging.info("Output directory is writable")
        except Exception as e:
            logging.error(f"Output directory is not writable: {e}")
            
    except Exception as e:
        logging.error(f"Error creating output directory: {e}")
        raise

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

def handle_transcription(
    recorder: AudioRecorder,
    transcriber: WhisperTranscriber,
    copy_to_clipboard: bool = False,
    output_file: str = None,
    use_kokoro: bool = False,
    use_llm: bool = False,
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
        
    Returns:
        bool: False if exit command detected, True otherwise
    """
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
    result = transcriber.transcribe_audio(audio_data)
    if result is None:
        logging.error("Transcription failed")
        return True

    # Get transcribed text
    text = transcriber.get_transcribed_text(result)
    if text:
        logging.info(f"Transcription: {text}")

        # Handle clipboard copy
        if copy_to_clipboard:
            pyperclip.copy(text)
            logging.info("Text copied to clipboard")

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
                    save_transcription(llm_response, LLM_OUTPUT_FILENAME)
            except Exception as e:
                logging.error(f"Error in LLM processing: {e}")

        # Handle Kokoro conversion
        if use_kokoro:
            try:
                kokoro_handler = KokoroHandler()
                output_path = kokoro_handler.convert_text_to_speech(text)
                if output_path:
                    logging.info(f"Text-to-speech conversion saved to: {output_path}")
            except Exception as e:
                logging.error(f"Error in Kokoro conversion: {e}")

    return True

def main():
    """Main function to run the speech-to-text application."""
    parser = argparse.ArgumentParser(
        description="Real-time speech-to-text transcription program."
    )
    parser.add_argument(
        "--single",
        action="store_true",
        help="Capture a single speech input and exit"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        help="Specify a file to save the transcription output"
    )
    parser.add_argument(
        "--copy",
        action="store_true",
        help="Copy transcription to clipboard"
    )
    parser.add_argument(
        "--kokoro",
        action="store_true",
        help="Enable Kokoro text-to-speech conversion"
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Enable LLM processing of transcribed text"
    )
    args = parser.parse_args()

    # Set up logging
    setup_logging()

    # Verify output directory at startup
    logging.info("=== Application Initialization ===")
    logging.info(f"Current working directory: {os.getcwd()}")
    verify_output_directory()

    try:
        with AudioRecorder() as recorder:
            # Calibrate silence threshold
            recorder.calibrate_silence_threshold()
            
            # Initialize transcriber
            transcriber = WhisperTranscriber()

            if args.single:
                # Single transcription mode
                handle_transcription(
                    recorder,
                    transcriber,
                    copy_to_clipboard=args.copy,
                    output_file=args.output_file,
                    use_kokoro=args.kokoro,
                    use_llm=args.llm
                )
            else:
                # Continuous transcription mode
                while True:
                    if not handle_transcription(
                        recorder,
                        transcriber,
                        copy_to_clipboard=args.copy,
                        output_file=MLXW_OUTPUT_FILENAME,
                        use_kokoro=args.kokoro,
                        use_llm=args.llm
                    ):
                        break
                    logging.info("Press Enter to start listening again...")
                    input()

    except KeyboardInterrupt:
        logging.info("\nExiting program.")

if __name__ == "__main__":
    main()