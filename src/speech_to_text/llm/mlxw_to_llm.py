# File: src/speech_to_text/llm/mlxw_to_llm.py
"""
Alternative LLM integration for processing transcribed text.
Implements a simpler request structure matching direct API calls.
"""

import logging
import os
import requests
from typing import Optional

from speech_to_text.config.settings import (
    LLM_BASE_URL,
    LLM_MODEL,
    LLM_OUTPUT_FILENAME,
    OUTPUT_DIR
)

class MLXWToLLM:
    """Handles sending transcribed text to LLM using direct API calls."""
    
    def __init__(self):
        """Initialize the LLM handler."""
        self._ensure_output_directory()
        
    def _ensure_output_directory(self) -> None:
        """Ensure the output directory exists."""
        try:
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            logging.debug(f"Output directory verified: {OUTPUT_DIR}")
            logging.debug(f"LLM output file will be: {LLM_OUTPUT_FILENAME}")
        except Exception as e:
            logging.error(f"Error creating output directory: {e}")
            raise

    def _save_response(self, response_text: str) -> None:
        """
        Save LLM response to output file.
        
        Args:
            response_text: Response text to save
        """
        try:
            logging.debug(f"Attempting to save response to: {LLM_OUTPUT_FILENAME}")
            
            # Verify the path
            if not LLM_OUTPUT_FILENAME or LLM_OUTPUT_FILENAME.endswith('/'):
                logging.error(f"Invalid LLM output filename: {LLM_OUTPUT_FILENAME}")
                return
                
            # Ensure the directory exists
            output_dir = os.path.dirname(LLM_OUTPUT_FILENAME)
            os.makedirs(output_dir, exist_ok=True)

            # Write the response
            with open(LLM_OUTPUT_FILENAME, 'a', encoding='utf-8') as f:
                f.write(f"\nResponse: {response_text}\n")
                f.write("-" * 50 + "\n")
            logging.info(f"Response saved to: {LLM_OUTPUT_FILENAME}")
        except Exception as e:
            logging.error(f"Error saving response to file: {e}")
            logging.error(f"Attempted file path: {LLM_OUTPUT_FILENAME}")
            logging.error(f"Output directory exists: {os.path.exists(output_dir)}")
            logging.error(f"Output directory is writable: {os.access(output_dir, os.W_OK)}")

    def process_text(self, text: str) -> Optional[str]:
        """
        Send text to LLM and process response.
        
        Args:
            text: Text to send to LLM
            
        Returns:
            Optional[str]: Processed LLM response if successful, None otherwise
        """
        if not text:
            logging.error("No text provided for LLM processing")
            return None
            
        try:
            # Prepare request payload
            payload = {
                "model": LLM_MODEL,
                "messages": [
                    {"role": "user", "content": text}
                ],
                "temperature": 0.7,
                "max_tokens": -1,
                "stream": False
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            # Log request details
            logging.debug(f"Making request to LLM API - URL: {LLM_BASE_URL}/chat/completions")
            logging.debug(f"Request parameters - Model: {LLM_MODEL}")
            
            # Make request to LLM API
            response = requests.post(
                f"{LLM_BASE_URL}/chat/completions",
                headers=headers,
                json=payload
            )
            
            # Check if request was successful
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            response_text = result["choices"][0]["message"]["content"]
            
            # Save response to file
            self._save_response(response_text)
            
            return response_text
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error during LLM API request: {e}")
            return None
        except Exception as e:
            logging.error(f"Error during LLM processing: {e}")
            return None