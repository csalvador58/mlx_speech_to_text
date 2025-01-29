# File: src/speech_to_text/kokoro/mlxw_to_kokoro.py
"""
Kokoro text-to-speech integration for converting transcribed text to speech.
Handles the conversion of text to speech using the Kokoro API.
"""

import logging
import os
import re
from typing import Optional
import pyaudio
from openai import OpenAI

from speech_to_text.config.settings import (
    KOKORO_BASE_URL,
    KOKORO_API_KEY,
    KOKORO_MODEL,
    KOKORO_VOICE,
    KOKORO_RESPONSE_FORMAT,
    KOKORO_OUTPUT_FILENAME,
    OUTPUT_DIR,
)
from speech_to_text.config import (
    WORD_REPLACEMENTS,
    PUNCTUATION_REPLACEMENTS,
    GLOBAL_REPLACEMENTS,
)

# Pre-processing patterns for specific formats
LIST_ITEM_PATTERN = re.compile(r'^\d+\.\s+')
MARKDOWN_BOLD_PATTERN = re.compile(r'\*\*(.+?)\*\*')
MARKDOWN_ITALIC_PATTERN = re.compile(r'\*(.+?)\*')
MARKDOWN_LINK_PATTERN = re.compile(r'\[(.+?)\]\(.+?\)')
MARKDOWN_CODE_PATTERN = re.compile(r'`(.+?)`')

def optimize_for_voice(text: str) -> str:
    """
    Optimize text for voice synthesis by applying various text transformations.
    
    Args:
        text: Input text to optimize
        
    Returns:
        str: Optimized text ready for voice synthesis
    """
    # Pre-process markdown patterns
    def preprocess_markdown(text: str) -> str:
        """Remove markdown formatting while preserving content."""
        # Remove numbered list markers but keep the text
        text = LIST_ITEM_PATTERN.sub('', text)
        
        # Remove bold/italic markers but keep the text
        text = MARKDOWN_BOLD_PATTERN.sub(r'\1', text)
        text = MARKDOWN_ITALIC_PATTERN.sub(r'\1', text)
        
        # Convert links to just their text
        text = MARKDOWN_LINK_PATTERN.sub(r'\1', text)
        
        # Remove code markers
        text = MARKDOWN_CODE_PATTERN.sub(r'\1', text)
        
        return text

    def replace_word(match):
        """Replace matched word while preserving case."""
        word = match.group()
        replacement = WORD_REPLACEMENTS.get(word.lower())
        if replacement is None:
            return word
        # Preserve original case if the word was capitalized
        if word.isupper():
            return replacement.upper()
        if word[0].isupper():
            return replacement.capitalize()
        return replacement

    def replace_with_dict(text: str, replacements: dict, pattern: str) -> str:
        """Apply replacements using a given pattern."""
        def replace_match(match):
            char = match.group()
            return replacements.get(char, char)
        return re.sub(pattern, replace_match, text)

    # Step 1: Pre-process markdown formatting
    text = preprocess_markdown(text)
    
    # Step 2: Replace common abbreviations and technical terms
    word_pattern = r'\b(?<!\w)(' + '|'.join(re.escape(key) for key in WORD_REPLACEMENTS.keys()) + r')(?!\w)\b'
    text = re.sub(word_pattern, replace_word, text, flags=re.IGNORECASE)

    # Step 3: Handle punctuation (only when surrounded by spaces or at string boundaries)
    punct_pattern = (
        r'(?<=\s)[' + 
        re.escape(''.join(PUNCTUATION_REPLACEMENTS.keys())) + 
        r'](?=\s)|(?<=\s)[' +
        re.escape(''.join(PUNCTUATION_REPLACEMENTS.keys())) +
        r']|[' +
        re.escape(''.join(PUNCTUATION_REPLACEMENTS.keys())) +
        r'](?=\s)'
    )
    text = replace_with_dict(text, PUNCTUATION_REPLACEMENTS, punct_pattern)

    # Step 4: Apply global character replacements
    global_pattern = '[' + re.escape(''.join(GLOBAL_REPLACEMENTS.keys())) + ']'
    text = replace_with_dict(text, GLOBAL_REPLACEMENTS, global_pattern)

    # Step 5: Clean up multiple spaces and trim
    text = ' '.join(text.split())
    
    # Step 6: Add natural pauses between list items
    text = re.sub(r'(?<=\w)\.(?=\s+[A-Z])', '... ', text)
    
    return text

class KokoroHandler:
    """Handles text-to-speech conversion using the Kokoro API."""
    
    def __init__(self):
        """Initialize the Kokoro handler with OpenAI client."""
        self.client = OpenAI(
            base_url=KOKORO_BASE_URL,
            api_key=KOKORO_API_KEY
        )
        self._ensure_output_directory()
        
    def _ensure_output_directory(self) -> None:
        """Ensure the output directory exists."""
        try:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
        except Exception as e:
            logging.error(f"Error creating output directory: {e}")
            raise

    def convert_text_to_speech(self, text: str, optimize: bool = False) -> Optional[str]:
        """
        Convert text to speech using Kokoro API and save to file.
        
        Args:
            text: Text to convert to speech
            optimize: Whether to apply voice optimization to the text
            
        Returns:
            Optional[str]: Path to the output audio file if successful, None otherwise
        """
        if not text:
            logging.error("No text provided for text-to-speech conversion")
            return None

        try:
            if optimize:
                text = optimize_for_voice(text)
                logging.debug(f"Optimized text for voice: {text}")

            # Log request before making the API call
            logging.debug(f"Making request to Kokoro API - URL: {KOKORO_BASE_URL}/audio/speech")
            logging.debug(f"Request parameters - Model: {KOKORO_MODEL}, Voice: {KOKORO_VOICE}, Format: {KOKORO_RESPONSE_FORMAT}")
            
            with self.client.audio.speech.with_streaming_response.create(
                model=KOKORO_MODEL,
                voice=KOKORO_VOICE,
                input=text,
                response_format=KOKORO_RESPONSE_FORMAT
            ) as response:
                # Log successful response
                logging.debug(f"Received response from Kokoro API - Status: {response.status_code}")
                response.stream_to_file(KOKORO_OUTPUT_FILENAME)
                
            return KOKORO_OUTPUT_FILENAME
            
        except Exception as e:
            logging.error(f"Error during text-to-speech conversion: {e}")
            return None

    def stream_text_to_speakers(self, text: str, optimize: bool = False) -> bool:
        """
        Convert text to speech and stream directly to speakers.
        
        Args:
            text: Text to convert to speech
            optimize: Whether to apply voice optimization to the text
            
        Returns:
            bool: True if streaming was successful, False otherwise
        """
        if not text:
            logging.error("No text provided for text-to-speech streaming")
            return False
            
        try:
            if optimize:
                text = optimize_for_voice(text)
                logging.debug(f"Optimized text for voice: {text}")

            # Initialize PyAudio
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=24000,
                output=True
            )
            
            logging.debug(f"Making streaming request to Kokoro API - URL: {KOKORO_BASE_URL}/audio/speech")
            logging.debug(f"Request parameters - Model: {KOKORO_MODEL}, Voice: {KOKORO_VOICE}, Format: pcm")
            
            with self.client.audio.speech.with_streaming_response.create(
                model=KOKORO_MODEL,
                voice=KOKORO_VOICE,
                input=text,
                response_format="pcm"  # Use PCM format for direct streaming
            ) as response:
                logging.debug(f"Received streaming response from Kokoro API - Status: {response.status_code}")
                
                # Stream chunks to speakers
                for chunk in response.iter_bytes(chunk_size=1024):
                    stream.write(chunk)
                
            # Clean up
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
            logging.info("Successfully streamed text to speakers")
            return True
            
        except Exception as e:
            logging.error(f"Error during text-to-speech streaming: {e}")
            return False