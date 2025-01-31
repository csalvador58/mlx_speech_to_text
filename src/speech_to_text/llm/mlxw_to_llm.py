# File: src/speech_to_text/llm/mlxw_to_llm.py
"""
Alternative LLM integration for processing transcribed text.
Implements a simpler request structure matching direct API calls.
"""

import logging
import requests
from typing import Optional, List, Dict, Any, Tuple

from speech_to_text.config.settings import (
    LLM_BASE_URL,
    LLM_MODEL,
    LLM_OUTPUT_FILENAME,
    OUTPUT_DIR
)
from speech_to_text.utils.path_utils import (
    ensure_directory,
    safe_write_file
)

class MLXWToLLM:
    """Handles sending transcribed text to LLM using direct API calls."""
    
    def __init__(self):
        """Initialize the LLM handler."""
        self._ensure_output_directory()
        
    def _ensure_output_directory(self) -> None:
        """Ensure the output directory exists."""
        if not ensure_directory(OUTPUT_DIR):
            raise RuntimeError(f"Failed to create/verify output directory: {OUTPUT_DIR}")
        logging.debug(f"Output directory verified: {OUTPUT_DIR}")
        logging.debug(f"LLM output file will be: {LLM_OUTPUT_FILENAME}")

    def _save_response(self, response_text: str) -> None:
        """
        Save LLM response to output file.
        
        Args:
            response_text: Response text to save
        """
        content = f"\nResponse: {response_text}\n{'-' * 50}\n"
        if safe_write_file(content, LLM_OUTPUT_FILENAME, append=True):
            logging.info(f"Response saved to: {LLM_OUTPUT_FILENAME}")
        else:
            logging.error(f"Failed to save response to: {LLM_OUTPUT_FILENAME}")

    def _prepare_messages(self, current_text: str, message_history: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Prepare messages array for LLM request, ensuring system messages are positioned correctly.
        
        Args:
            current_text: Current message to process
            message_history: List of previous messages
            
        Returns:
            List[Dict[str, str]]: Properly ordered messages for LLM request
        """
        # Extract system messages
        system_messages = [msg for msg in message_history if msg.get('role') == 'system']
        
        # Extract conversation messages (non-system)
        conversation = [msg for msg in message_history if msg.get('role') != 'system']
        
        # Combine in correct order: system messages first, then conversation, then current message
        messages = []
        messages.extend(system_messages)  # System messages always first
        messages.extend(conversation)     # Previous conversation
        messages.append({"role": "user", "content": current_text})  # Current message
        
        # Log message structure
        logging.debug(f"Prepared messages structure:")
        logging.debug(f"- System messages: {len(system_messages)}")
        logging.debug(f"- Conversation messages: {len(conversation)}")
        
        return messages

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

    def process_chat(
        self,
        text: str,
        message_history: List[Dict[str, str]]
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Process a chat message with conversation history.
        
        Args:
            text: Current message to process
            message_history: List of previous messages in the conversation
            
        Returns:
            Tuple[Optional[str], Optional[Dict[str, Any]]]:
                - Response text if successful, None otherwise
                - Complete LLM response object if successful, None otherwise
        """
        if not text:
            logging.error("No text provided for chat processing")
            return None, None
            
        try:
            # Prepare messages with correct ordering
            messages = self._prepare_messages(text, message_history)
            
            # Prepare request payload
            payload = {
                "model": LLM_MODEL,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": -1,
                "stream": False
            }
            
            headers = {
                "Content-Type": "application/json"
            }
            
            # Log request details
            logging.debug(f"Making chat request to LLM API - URL: {LLM_BASE_URL}/chat/completions")
            logging.debug(f"Chat history length: {len(message_history)}")
            
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
            
            return response_text, result
            
        except requests.exceptions.RequestException as e:
            logging.error(f"Error during chat API request: {e}")
            return None, None
        except Exception as e:
            logging.error(f"Error during chat processing: {e}")
            return None, None