# File: src/speech_to_text/chat/chat_history.py
"""
Chat history management for the speech-to-text application.
Handles saving, loading, and updating chat conversations.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from speech_to_text.config.settings import (
    CHAT_HISTORY_DIR,
    CHAT_PREVIEW_MAX_LENGTH,
    CHAT_FILE_EXTENSION,
)
from speech_to_text.utils.path_utils import (
    ensure_directory,
    validate_file_path,
    safe_read_file,
    safe_write_file,
    safe_list_files,
)


class ChatHistory:
    """Manages chat history storage and retrieval."""

    def __init__(self):
        """Initialize the chat history manager."""
        self._ensure_history_directory()
        self.current_chat_id: Optional[str] = None
        self.messages: List[Dict[str, str]] = []

    def _ensure_history_directory(self) -> None:
        """Ensure the chat history directory exists."""
        if not ensure_directory(CHAT_HISTORY_DIR):
            raise RuntimeError(
                f"Failed to create/verify chat history directory: {CHAT_HISTORY_DIR}"
            )
        logging.debug(f"Chat history directory verified: {CHAT_HISTORY_DIR}")

    def _get_history_file_path(self, chat_id: str) -> Optional[Path]:
        """
        Get the validated file path for a chat history file.

        Args:
            chat_id: The chat ID to get the path for

        Returns:
            Optional[Path]: Validated Path object or None if validation fails
        """
        file_path = Path(CHAT_HISTORY_DIR) / f"{chat_id}{CHAT_FILE_EXTENSION}"
        return validate_file_path(file_path)

    def _extract_preview(self, messages: List[Dict[str, str]]) -> str:
        """
        Extract preview text from the last chat message.
        
        Args:
            messages: List of chat messages
        
        Returns:
            str: Preview text or empty string if no messages found
        """
        if not messages:
            return ""
        
        # Get the last message's content
        last_message = messages[-1]
        content = last_message.get("content", "")
        
        # Truncate and add ellipsis if needed
        return content[:CHAT_PREVIEW_MAX_LENGTH] + (
            "..." if len(content) > CHAT_PREVIEW_MAX_LENGTH else ""
        )

    def get_chat_list(self) -> List[Dict[str, Any]]:
        """
        Get list of available chat sessions sorted by modification time.
        
        Returns:
            List[Dict[str, Any]]: List of chat information dictionaries containing:
                - id: Chat ID
                - modified: Modification timestamp
                - preview: Preview of first user message
        """
        try:
            # Get all JSON files from chat history directory
            files = safe_list_files(CHAT_HISTORY_DIR)
            
            chat_files = []
            for file in files:
                try:
                    # Get file metadata
                    mod_time = os.path.getmtime(file)
                    chat_id = file.stem
                    
                    # Read chat content for preview
                    content = safe_read_file(file)
                    preview = ""
                    if content:
                        try:
                            data = json.loads(content)
                            messages = data.get("messages", [])
                            preview = self._extract_preview(messages)
                        except json.JSONDecodeError:
                            logging.warning(f"Could not parse chat history file: {file}")
                    
                    chat_files.append({
                        "id": chat_id,
                        "modified": mod_time,
                        "preview": preview
                    })
                except Exception as e:
                    logging.warning(f"Error processing chat file {file}: {e}")
                    continue

            # Sort by modification time (newest first)
            return sorted(chat_files, key=lambda x: x["modified"], reverse=True)
            
        except Exception as e:
            logging.error(f"Error getting chat list: {e}")
            return []

    def load_history(self, chat_id: str) -> bool:
        """
        Load chat history from file.

        Args:
            chat_id: ID of the chat history to load

        Returns:
            bool: True if history was loaded successfully, False otherwise
        """
        try:
            file_path = self._get_history_file_path(chat_id)
            if not file_path or not file_path.exists():
                logging.error(f"Chat history file not found: {chat_id}")
                return False

            content = safe_read_file(file_path)
            if not content:
                return False

            history = json.loads(content)
            self.messages = history.get("messages", [])
            self.current_chat_id = chat_id
            logging.info(f"Loaded chat history for ID: {chat_id}")
            return True

        except json.JSONDecodeError as e:
            logging.error(f"Error parsing chat history JSON: {e}")
            return False
        except Exception as e:
            logging.error(f"Error loading chat history: {e}")
            return False

    def save_history(self) -> bool:
        """
        Save current chat history to file.

        Returns:
            bool: True if history was saved successfully, False otherwise
        """
        if not self.current_chat_id:
            return False

        try:
            file_path = self._get_history_file_path(self.current_chat_id)
            if not file_path:
                return False

            history = {"chat_id": self.current_chat_id, "messages": self.messages}

            content = json.dumps(history, indent=2)
            if safe_write_file(content, file_path):
                logging.info(f"Saved chat history to: {file_path}")
                return True
            return False

        except Exception as e:
            logging.error(f"Error saving chat history: {e}")
            return False

    def initialize_from_llm_response(
        self, llm_response: Dict[str, Any], user_message: str
    ) -> None:
        """
        Initialize a new chat history from an LLM response while preserving system messages.

        Args:
            llm_response: Complete response from LLM API
            user_message: The user's initial message
        """
        try:
            # Extract chat ID from response
            chat_id = llm_response.get("id")
            if not chat_id:
                logging.error("No chat ID found in LLM response")
                return

            # Preserve any existing system messages
            system_messages = [
                msg for msg in self.messages if msg.get("role") == "system"
            ]

            # Initialize new message array with system messages first
            new_messages = []

            # Add system messages if they exist
            if system_messages:
                new_messages.extend(system_messages)
                logging.debug(f"Preserved {len(system_messages)} system message(s)")

            # Add the initial user/assistant exchange
            new_messages.extend(
                [
                    {"role": "user", "content": user_message},
                    {
                        "role": "assistant",
                        "content": llm_response["choices"][0]["message"]["content"],
                    },
                ]
            )

            # Update chat state
            self.current_chat_id = chat_id
            self.messages = new_messages

            # Save initial history
            self.save_history()
            logging.info(f"Initialized new chat history with ID: {chat_id}")

        except Exception as e:
            logging.error(f"Error initializing chat history: {e}")

    def add_message(self, role: str, content: str) -> None:
        """
        Add a new message to the chat history.

        Args:
            role: Role of the message sender ("user" or "assistant")
            content: Content of the message
        """
        if not self.current_chat_id:
            return

        self.messages.append({"role": role, "content": content})
        self.save_history()
        logging.debug(f"Added {role} message to chat history")

    @property
    def message_history(self) -> List[Dict[str, str]]:
        """
        Get the current message history.

        Returns:
            List[Dict[str, str]]: List of message dictionaries
        """
        return self.messages