# File: src/speech_to_text/llm/mlxw_to_llm.py
"""
Alternative LLM integration for processing transcribed text.
Implements a simpler request structure matching direct API calls.
"""

import logging
import json
import requests
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

from .file_handler import process_file, prepare_content_message
from speech_to_text.config.settings import (
    LLM_BASE_URL,
    LLM_MODEL,
    LLM_MAX_TOKENS,
    LLM_TEMPERATURE,
    LLM_OUTPUT_FILENAME,
    LLM_REQUEST_TIMEOUT,
    OUTPUT_DIR,
)
from speech_to_text.utils.path_utils import ensure_directory, safe_write_file


class MLXWToLLM:
    """Handles sending transcribed text to LLM using direct API calls."""

    def __init__(self):
        """Initialize the LLM handler."""
        self._ensure_output_directory()
        self._validate_llm_connection()

    def _ensure_output_directory(self) -> None:
        """Ensure the output directory exists."""
        if not ensure_directory(OUTPUT_DIR):
            raise RuntimeError(
                f"Failed to create/verify output directory: {OUTPUT_DIR}"
            )
        logging.debug(f"Output directory verified: {OUTPUT_DIR}")
        logging.debug(f"LLM output file will be: {LLM_OUTPUT_FILENAME}")

    def _validate_llm_connection(self) -> None:
        """Validate LLM API connection and compatibility."""
        try:
            # Test connection with a simple request
            response = requests.get(f"{LLM_BASE_URL}/models", timeout=LLM_REQUEST_TIMEOUT)
            response.raise_for_status()

            # Check if model is available
            models = response.json()
            available_models = [model.get("id", "") for model in models.get("data", [])]

            if LLM_MODEL not in available_models:
                logging.warning(
                    f"Configured model '{LLM_MODEL}' not found in available models: {available_models}"
                )
                logging.warning("Available models:")
                for model in available_models:
                    logging.warning(f"  - {model}")

            logging.info(f"LLM API connection validated. Using model: {LLM_MODEL}")

        except requests.exceptions.RequestException as e:
            logging.error(f"Failed to validate LLM connection: {e}")
            logging.warning("Continuing without validation, but API calls may fail")
        except Exception as e:
            logging.error(f"Unexpected error during LLM validation: {e}")
            logging.warning("Continuing without validation, but API calls may fail")

    def _prepare_messages(
        self, 
        current_text: str, 
        message_history: List[Dict[str, str]],
        doc_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Prepare messages array for LLM request, adding document context if provided.

        Args:
            current_text: Current message to process
            message_history: List of previous messages
            doc_path: Optional path to document for analysis

        Returns:
            List[Dict[str, Any]]: Properly ordered messages for LLM request
        """
        if not current_text.strip():
            logging.warning("Empty current text provided")
            return []

        messages = []

        # Process document if provided
        if doc_path:
            processed_content, is_image = process_file(doc_path)
            if processed_content:
                if is_image:
                    # For images, add as user message
                    doc_message = prepare_content_message(processed_content, is_image=True)
                else:
                    # For text/PDF, add as system message
                    doc_message = {
                        "role": "system",
                        "content": (
                            f"<<DOCUMENT CONTEXT>>\n{processed_content}\n<<END DOCUMENT CONTEXT>>\n\n"
                            "Consider the above document context when responding to queries. "
                            "You can reference specific parts when relevant."
                        )
                    }
                messages.append(doc_message)
                logging.info(f"Added document context from: {doc_path}")

        # Extract and validate system messages from history
        system_messages = [
            msg for msg in message_history if msg.get("role") == "system"
        ]

        # Extract conversation messages (non-system)
        conversation = [msg for msg in message_history if msg.get("role") != "system"]

        # Combine in correct order: system messages first, then conversation, then current message
        messages.extend(system_messages)  # System messages always first
        messages.extend(conversation)  # Previous conversation
        messages.append({"role": "user", "content": current_text})  # Current message

        # Log message structure
        logging.debug(f"Prepared messages structure:")
        logging.debug(f"- Document context: {'Yes' if doc_path else 'No'}")
        logging.debug(f"- System messages: {len(system_messages)}")
        logging.debug(f"- Conversation messages: {len(conversation)}")
        logging.debug(f"- Total messages: {len(messages)}")

        return messages

    def process_chat(
        self, 
        text: str, 
        message_history: List[Dict[str, str]],
        doc_path: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
        """
        Process a chat message with conversation history and optional document context.

        Args:
            text: Current message to process
            message_history: List of previous messages in the conversation
            doc_path: Optional path to document for analysis

        Returns:
            Tuple[Optional[str], Optional[Dict[str, Any]]]:
                - Response text if successful, None otherwise
                - Complete LLM response object if successful, None otherwise
        """
        if not text:
            logging.error("No text provided for chat processing")
            return None, None

        try:
            # Prepare messages with correct ordering and document context
            messages = self._prepare_messages(text, message_history, doc_path)
            if not messages:
                return None, None

            # Prepare request payload
            payload = {
                "model": LLM_MODEL,
                "messages": messages,
                "temperature": LLM_TEMPERATURE,
                "max_tokens": LLM_MAX_TOKENS,
                "stream": False,
            }

            headers = {"Content-Type": "application/json"}

            # Log request details for debugging
            logging.debug(
                f"Making chat request to LLM API - URL: {LLM_BASE_URL}/chat/completions"
            )
            if doc_path:
                logging.debug(f"Including document context from: {doc_path}")

            # Make request to LLM API with configured timeout
            response = requests.post(
                f"{LLM_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=LLM_REQUEST_TIMEOUT
            )

            # Better error handling with response content
            if response.status_code != 200:
                error_msg = f"LLM API error: {response.status_code}"
                try:
                    error_data = response.json()
                    error_details = error_data.get("error", {})
                    if isinstance(error_details, dict):
                        error_msg = f"{error_msg} - {error_details.get('message', 'Unknown error')}"
                    else:
                        error_msg = f"{error_msg} - {error_details}"
                except:
                    error_msg = f"{error_msg} - {response.text[:500]}"  # Limit error text length
                logging.error(error_msg)
                return None, None

            # Parse response
            result = response.json()

            # Validate response structure
            if not isinstance(result, dict) or "choices" not in result:
                logging.error(f"Invalid response structure: {result}")
                return None, None

            if not result["choices"] or "message" not in result["choices"][0]:
                logging.error("No choices or message in response")
                return None, None

            response_text = result["choices"][0]["message"]["content"]

            # Save response to file
            self._save_response(response_text)

            return response_text, result

        except requests.exceptions.Timeout:
            logging.error(f"LLM API request timed out after {LLM_REQUEST_TIMEOUT} seconds")
            return None, None
        except requests.exceptions.RequestException as e:
            logging.error(f"Error during chat API request: {e}")
            return None, None
        except Exception as e:
            logging.error(f"Error during chat processing: {e}")
            return None, None

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
            # Process as a single message chat
            response_text, _ = self.process_chat(text, [], doc_path=None)
            return response_text

        except Exception as e:
            logging.error(f"Error during LLM processing: {e}")
            return None