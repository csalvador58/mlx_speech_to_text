# File: main.py
"""
Main entry point for the speech-to-text application.
Handles command line arguments and orchestrates the transcription process.
"""

import argparse
import logging
import pyperclip

from speech_to_text.audio.recorder import AudioRecorder
from speech_to_text.transcriber.whisper import WhisperTranscriber
from speech_to_text.utils.logging import setup_logging

def save_transcription(text: str, output_file: str) -> None:
    """Save transcription to a file."""
    try:
        with open(output_file, 'w') as f:
            f.write(text)
        logging.info(f"Transcription saved to {output_file}")
    except Exception as e:
        logging.error(f"Error saving transcription to file: {e}")

def handle_transcription(
    recorder: AudioRecorder,
    transcriber: WhisperTranscriber,
    copy_to_clipboard: bool = False,
    output_file: str = None
) -> bool:
    """
    Handle a single transcription cycle.
    
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
    args = parser.parse_args()

    # Set up logging
    setup_logging()

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
                    output_file=args.output_file
                )
            else:
                # Continuous transcription mode
                while True:
                    if not handle_transcription(
                        recorder,
                        transcriber,
                        copy_to_clipboard=args.copy
                    ):
                        break
                    logging.info("Press Enter to start listening again...")
                    input()

    except KeyboardInterrupt:
        logging.info("\nExiting program.")

if __name__ == "__main__":
    main()