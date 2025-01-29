# File: src/speech_to_text/utils/logging.py
"""
Logging configuration for the speech-to-text application.
Sets up logging with consistent formatting across the application.
"""

import logging
from speech_to_text.config.settings import LOG_FORMAT, LOG_LEVEL

def setup_logging() -> None:
    """
    Configure logging for the application.
    Sets up console logging with the specified format and level.
    """
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL),
        format=LOG_FORMAT
    )
    
    # Create logger
    logger = logging.getLogger('speech_to_text')
    
    # Avoid duplicate handlers
    if not logger.handlers:
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(getattr(logging, LOG_LEVEL))
        
        # Create formatter
        formatter = logging.Formatter(LOG_FORMAT)
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)