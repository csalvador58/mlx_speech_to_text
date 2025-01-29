# File: src/main.py
"""
Main entry point for the speech-to-text application.
Handles command line arguments and orchestrates the transcription process.
"""

import argparse
import logging
import os
from pathlib import Path

from speech_to_text.audio.recorder import AudioRecorder
from speech_to_text.transcriber.whisper import WhisperTranscriber
from speech_to_text.utils import (
    setup_logging,
    handle_transcription
)
from speech_to_text.chat import ChatHandler
from speech_to_text.config.settings import (
    MLXW_OUTPUT_FILENAME,
    OUTPUT_DIR
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
    parser.add_argument(
        "--chat",
        action="store_true",
        help="Enable interactive chat mode with LLM"
    )
    parser.add_argument(
        "--chat-id",
        type=str,
        help="Continue an existing chat session"
    )
    args = parser.parse_args()

    # Set up logging
    setup_logging()

    # Verify output directory at startup
    logging.info("=== Application Initialization ===")
    logging.info(f"Current working directory: {os.getcwd()}")
    verify_output_directory()

    # Initialize chat handler if needed
    chat_handler = None
    if args.chat:
        chat_handler = ChatHandler()
        if args.chat_id:
            if not chat_handler.load_existing_chat(args.chat_id):
                logging.error(f"Failed to load chat session: {args.chat_id}")
                return
            logging.info(f"Resumed chat session: {args.chat_id}")
        else:
            chat_handler.start_new_chat()
            logging.info("Started new chat session")

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
                    use_llm=args.llm,
                    chat_handler=chat_handler
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
                        use_llm=args.llm,
                        chat_handler=chat_handler
                    ):
                        break
                    logging.info("Press Enter to start listening again...")
                    input()

    except KeyboardInterrupt:
        logging.info("\nExiting program.")

if __name__ == "__main__":
    main()