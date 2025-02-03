# File: src/speech_to_text/api/connect.py

from flask import Blueprint
from .connect_copy import copy_bp
from .connect_chat import chat_bp
from .connect_status import status_bp

# Create main connect blueprint
connect_bp = Blueprint("connect", __name__)

# Register route blueprints
connect_bp.register_blueprint(copy_bp, url_prefix="/copy")
connect_bp.register_blueprint(chat_bp, url_prefix="/chat")
connect_bp.register_blueprint(status_bp, url_prefix="/status")
