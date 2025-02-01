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
from speech_to_text.utils.path_utils import (
    ensure_directory,
    validate_file_path,
    safe_read_file
)
from speech_to_text.chat import ChatHandler
from speech_to_text.config.settings import (
    MLXW_OUTPUT_FILENAME,
    OUTPUT_DIR
)

def verify_output_directory() -> None:
    """Verify and create output directory if it doesn't exist."""
    if not ensure_directory(OUTPUT_DIR):
        raise RuntimeError(f"Failed to create/verify output directory: {OUTPUT_DIR}")
    logging.info(f"Output directory verified/created: {OUTPUT_DIR}")

def validate_doc_path(doc_path: str) -> bool:
    """
    Validate document path for analysis.
    
    Args:
        doc_path: Path to document file
        
    Returns:
        bool: True if document is valid and readable
    """
    content = safe_read_file(doc_path)
    if not content:
        return False
        
    # Preview document content
    lines = content.splitlines()
    preview_lines = lines[:10]
    preview = '\n'.join(preview_lines)
    logging.debug(f"Document preview (first 10 lines):\n{preview}\n...")
    logging.info(f"Document validated: {validate_file_path(doc_path)}")
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
        help="Enable Kokoro text-to-speech conversion and saves to audio file"
    )
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Enable text optimization for voice synthesis"
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
        "--chat-voice",
        action="store_true",
        help="Enable interactive chat mode with voice responses streamed to speakers"
    )
    parser.add_argument(
        "--chat-voice-save",
        action="store_true",
        help="Enable interactive chat mode with voice responses streamed to speakers and saved to file"
    )
    parser.add_argument(
        "--chat-id",
        type=str,
        help="Continue an existing chat session"
    )
    parser.add_argument(
        "--doc",
        type=str,
        help="Path to text file to analyze in chat mode (supports ~ for home directory)"
    )
    args = parser.parse_args()

    # Set up logging
    setup_logging()

    # Verify output directory at startup
    logging.info("=== Application Initialization ===")
    logging.info(f"Current working directory: {os.getcwd()}")
    verify_output_directory()

    # Validate document if provided
    if args.doc and not validate_doc_path(args.doc):
        return

    # Initialize chat handler if needed
    chat_handler = None
    if args.chat or args.chat_voice or args.chat_voice_save:
        chat_handler = ChatHandler()
        if args.chat_id:
            if not chat_handler.load_existing_chat(args.chat_id):
                logging.error(f"Failed to load chat session: {args.chat_id}")
                return
            logging.info(f"Resumed chat session: {args.chat_id}")
        else:
            chat_handler.start_new_chat(doc_path=args.doc)
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
                    chat_handler=chat_handler,
                    stream_to_speakers=args.chat_voice or args.chat_voice_save,
                    save_to_file=args.chat_voice_save,
                    optimize_voice=args.optimize
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
                        chat_handler=chat_handler,
                        stream_to_speakers=args.chat_voice or args.chat_voice_save,
                        save_to_file=args.chat_voice_save,
                        optimize_voice=args.optimize
                    ):
                        break
                    logging.info("Press Enter to start listening again...")
                    input()

    except KeyboardInterrupt:
        logging.info("\nExiting program.")

if __name__ == "__main__":
    main()