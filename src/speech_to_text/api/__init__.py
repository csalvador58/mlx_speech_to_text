# File: src/speech_to_text/api/__init__.py
"""
API package to access app endpoints.
Provides REST endpoints for speech-to-text functionality:

Routes:
- /api/connect/copy: Convert speech to text and copy to clipboard
- /api/connect/chat: Convert speech to text and process through chat
- /api/connect/status: Stream status updates for ongoing operations
"""

from .connect_copy import copy_bp
from .connect_chat import chat_bp
from .connect_status import status_bp
