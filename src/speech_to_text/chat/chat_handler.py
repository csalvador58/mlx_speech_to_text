# File: src/speech_to_text/chat/chat_handler.py
"""
Chat workflow orchestration for the speech-to-text application.
Coordinates between speech recognition, LLM processing, and text-to-speech components.
"""

import logging
from typing import Optional, Tuple

from speech_to_text.chat.chat_history import ChatHistory
from speech_to_text.llm.mlxw_to_llm import MLXWToLLM
from speech_to_text.kokoro.mlxw_to_kokoro import KokoroHandler
from speech_to_text.utils.path_utils import safe_read_file

class ChatHandler:
    """Orchestrates chat interactions between components."""
    
    def __init__(self):
        """Initialize chat components."""
        self.chat_history = ChatHistory()
        self.llm_handler = MLXWToLLM()
        self.kokoro_handler = KokoroHandler()

    def _load_document(self, doc_path: str) -> Optional[str]:
        """
        Load document content for analysis.
        
        Args:
            doc_path: Path to the document
            
        Returns:
            Optional[str]: Document content if successful, None otherwise
        """
        content = safe_read_file(doc_path)
        if content:
            # Log document preview
            lines = content.splitlines()
            preview_lines = lines[:10]
            preview = '\n'.join(preview_lines)
            logging.info(f"Loaded document content preview:\n{preview}\n...")
            logging.info(f"Total lines in document: {len(lines)}")
            logging.info("Document loaded successfully, sending to LLM to analyze...")
        return content
        
    def process_message(
        self,
        text: str,
        use_kokoro: bool = False,
        stream_to_speakers: bool = False,
        save_to_file: bool = True,
        optimize_voice: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Process a new chat message.
        
        Args:
            text: Text message to process
            use_kokoro: Whether to convert response to speech file
            stream_to_speakers: Whether to stream response to speakers
            save_to_file: Whether to save audio responses to file
            optimize_voice: Whether to apply voice optimization
            
        Returns:
            Tuple[bool, Optional[str]]:
                - Success status
                - Response text if successful, None otherwise
        """
        try:
            # Check for exit command
            if text.strip().lower() in ['exit', 'quit', 'stop']:
                logging.info("Exit command received in chat")
                return False, None
            
            # Process with LLM
            if self.chat_history.current_chat_id:
                # Existing chat - use message history
                response_text, llm_response = self.llm_handler.process_chat(
                    text,
                    self.chat_history.message_history
                )
                if response_text and llm_response:
                    # Add messages to history
                    self.chat_history.add_message("user", text)
                    self.chat_history.add_message("assistant", response_text)
            else:
                # New chat - initialize history from response
                response_text, llm_response = self.llm_handler.process_chat(text, self.chat_history.messages)
                if response_text and llm_response:
                    self.chat_history.initialize_from_llm_response(llm_response, text)
            
            if not response_text:
                logging.error("Failed to get response from LLM")
                return True, None
            
            # Handle text-to-speech if enabled
            if use_kokoro or stream_to_speakers:
                try:
                    # Log response text for both streaming and conversion
                    logging.info(f"Processing text-to-speech: {response_text}")
                    
                    # Stream to speakers if requested
                    output_path = None
                    if stream_to_speakers:
                        output_path = self.kokoro_handler.stream_text_to_speakers(
                            response_text,
                            optimize=optimize_voice,
                            save_to_file=save_to_file
                        )
                        logging.info("Chat response streamed to speakers")
                    elif save_to_file:
                        # Only save to file if streaming is not enabled
                        output_path = self.kokoro_handler.convert_text_to_speech(
                            response_text,
                            optimize=optimize_voice
                        )
                        
                    if output_path and save_to_file:
                        logging.info(f"Chat response saved to file: {output_path}")
                        
                except Exception as e:
                    logging.error(f"Error in Kokoro conversion/streaming: {e}")
            
            return True, response_text
            
        except Exception as e:
            logging.error(f"Error processing chat message: {e}")
            return True, None
            
    def start_new_chat(self, doc_path: Optional[str] = None) -> None:
        """
        Reset chat state for a new conversation.
        
        Args:
            doc_path: Optional path to document file to initialize chat with
        """
        self.chat_history = ChatHistory()
        logging.info("Started new chat session")
        
        if doc_path:
            doc_content = self._load_document(doc_path)
            if doc_content:
                logging.debug("Adding document to chat history...")
                # Create new chat history with system message
                self.chat_history.messages = [{
                    "role": "system",
                    "content": f"<<START OF DOCUMENT>>\n{doc_content}\n<<END OF DOCUMENT>>"
                }]
                
                # Save history to ensure it's persisted
                self.chat_history.save_history()
                
                # Now send initial analysis request
                logging.debug("Sending initial document analysis request...")
                initial_prompt = (
                    "Analyze this document thoroughly so we can have discussion about it. "
                    "Make note of the titles, headers, and every section available."
                )
                success, response = self.process_message(initial_prompt)
                if not success:
                    logging.error("Failed to initialize chat with document context")
                elif response:
                    logging.info("Document analysis completed successfully")
        
    def load_existing_chat(self, chat_id: str) -> bool:
        """
        Load an existing chat session.
        
        Args:
            chat_id: ID of chat to load
            
        Returns:
            bool: True if chat was loaded successfully
        """
        return self.chat_history.load_history(chat_id)