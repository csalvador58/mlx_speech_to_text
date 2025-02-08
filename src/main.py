# File: src/main.py
"""
Main entry point for the speech-to-text application.
Supports both CLI and API server modes with document context handling.
"""

import argparse
import logging
import os
import signal
import sys
from pathlib import Path
from speech_to_text import create_app, __version__
from speech_to_text.audio.recorder import AudioRecorder
from speech_to_text.transcriber.whisper import WhisperTranscriber
from speech_to_text.utils import setup_logging, handle_transcription
from speech_to_text.utils.path_utils import (
    ensure_directory,
    validate_file_path,
    safe_read_file,
)
from speech_to_text.utils.api_utils import cleanup_session
from speech_to_text.chat import ChatHandler
from speech_to_text.config.settings import MLXW_OUTPUT_FILENAME, OUTPUT_DIR

app = create_app()

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logging.info(f"Received signal {signum}. Starting graceful shutdown...")
    cleanup_session()
    sys.exit(0)

@app.route("/")
def home():
    return {
        "message": "Welcome to the MLX Speech to Text API",
        "version": __version__,
        "endpoints": {
            "copy": "/api/connect/copy",
            "chat": "/api/connect/chat",
            "status": "/api/connect/status",
        },
    }

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
    if not doc_path:
        return True  # No document is valid

    path = validate_file_path(doc_path, must_exist=True)
    if not path:
        logging.error(f"Invalid document path or file not found: {doc_path}")
        return False

    content = safe_read_file(path)
    if not content:
        logging.error(f"Failed to read document or empty file: {doc_path}")
        return False

    lines = content.splitlines()
    preview_lines = lines[:10]
    preview = "\n".join(preview_lines)
    logging.debug(f"Document preview (first 10 lines):\n{preview}\n...")
    logging.info(f"Document validated: {doc_path}")
    return True

def run_cli(args):
    """
    Run the application in CLI mode.
    
    Supports document context with both new and existing chat sessions.
    Document context is applied per request without modifying chat history.
    """
    logging.info("=== Application Initialization (CLI Mode) ===")
    logging.info(f"Current working directory: {os.getcwd()}")
    verify_output_directory()

    # Validate document path if provided
    if args.doc and not validate_doc_path(args.doc):
        logging.error("Document validation failed. Exiting.")
        return

    # Initialize chat handler
    chat_handler = None
    if args.chat or args.chat_voice or args.chat_voice_save:
        chat_handler = ChatHandler()
        
        if args.chat_id:
            # Load existing chat session
            if not chat_handler.load_existing_chat(args.chat_id):
                logging.error(f"Failed to load chat session: {args.chat_id}")
                return
            logging.info(f"Resumed chat session: {args.chat_id}")
            
            # Log document context if provided
            if args.doc:
                logging.info(f"Using document context with existing chat: {args.doc}")
        else:
            # Start new chat session
            chat_handler.start_new_chat()
            logging.info("Started new chat session")
            
            if args.doc:
                logging.info(f"Using document context with new chat: {args.doc}")

    try:
        with AudioRecorder() as recorder:
            recorder.calibrate_silence_threshold()
            transcriber = WhisperTranscriber()

            if args.single:
                # Single transcription with document context
                success, error, response = handle_transcription(
                    recorder,
                    transcriber,
                    copy_to_clipboard=args.copy,
                    output_file=args.output_file,
                    use_kokoro=args.kokoro,
                    use_llm=args.llm,
                    chat_handler=chat_handler,
                    stream_to_speakers=args.chat_voice or args.chat_voice_save,
                    save_to_file=args.chat_voice_save,
                    optimize_voice=args.optimize,
                    doc_path=args.doc
                )
                
                if error:
                    logging.error(f"Transcription error: {error}")
                elif response and response.get("doc_path"):
                    logging.info(f"Processed with document context: {response['doc_path']}")
            else:
                # Continuous transcription loop
                while True:
                    success, error, response = handle_transcription(
                        recorder,
                        transcriber,
                        copy_to_clipboard=args.copy,
                        output_file=MLXW_OUTPUT_FILENAME,
                        use_kokoro=args.kokoro,
                        use_llm=args.llm,
                        chat_handler=chat_handler,
                        stream_to_speakers=args.chat_voice or args.chat_voice_save,
                        save_to_file=args.chat_voice_save,
                        optimize_voice=args.optimize,
                        doc_path=args.doc
                    )
                    
                    if not success:
                        if error:
                            logging.error(f"Transcription error: {error}")
                        break
                    
                    if response and response.get("doc_path"):
                        logging.info(f"Processed with document context: {response['doc_path']}")
                    
                    logging.info("Press Enter to start listening again...")
                    input()

    except KeyboardInterrupt:
        logging.info("\nExiting program.")


def run_server(port: int = 8081):
    """Run the application in API server mode."""
    logging.info("=== Application Initialization (API Mode) ===")
    logging.info(f"Starting server on port {port}")
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Enable threading for SSE
    app.run(host="0.0.0.0", port=port, debug=True, threaded=True)


def main():
    """Main function to parse arguments and run in appropriate mode."""
    parser = argparse.ArgumentParser(
        description=(
            "Real-time speech-to-text transcription program with CLI and API modes. "
            "Supports document context analysis for both new and existing chat sessions."
        )
    )

    # Server mode arguments
    parser.add_argument("--server", action="store_true", help="Run in API server mode")
    parser.add_argument(
        "--port",
        type=int,
        default=8081,
        help="Port number for API server (default: 8081)",
    )

    # Core functionality arguments
    parser.add_argument(
        "--single", action="store_true", help="Capture a single speech input and exit"
    )
    parser.add_argument(
        "--output-file",
        type=str,
        help="Specify a file to save the transcription output",
    )
    parser.add_argument(
        "--copy", action="store_true", help="Copy transcription to clipboard"
    )

    # Processing options
    parser.add_argument(
        "--kokoro", action="store_true", help="Enable Kokoro text-to-speech conversion"
    )
    parser.add_argument(
        "--optimize",
        action="store_true",
        help="Enable text optimization for voice synthesis",
    )
    parser.add_argument(
        "--llm", action="store_true", help="Enable LLM processing of transcribed text"
    )

    # Chat mode arguments
    chat_group = parser.add_argument_group("Chat Options")
    chat_group.add_argument(
        "--chat", action="store_true", help="Enable interactive chat mode with LLM"
    )
    chat_group.add_argument(
        "--chat-voice",
        action="store_true",
        help="Enable chat mode with voice responses streamed to speakers",
    )
    chat_group.add_argument(
        "--chat-voice-save",
        action="store_true",
        help="Enable chat mode with voice responses saved to file",
    )
    chat_group.add_argument(
        "--chat-id", 
        type=str, 
        help="Continue an existing chat session"
    )
    chat_group.add_argument(
        "--doc", 
        type=str, 
        help=(
            "Path to text file to analyze in chat mode. "
            "Can be used with new or existing chat sessions."
        )
    )

    args = parser.parse_args()
    setup_logging()

    try:
        if args.server:
            run_server(args.port)
        else:
            run_cli(args)
    except Exception as e:
        logging.error(f"Application error: {e}")
        cleanup_session()  # Ensure cleanup on error
        exit(1)


if __name__ == "__main__":
    main()