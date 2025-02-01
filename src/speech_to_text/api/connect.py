# File: src/speech_to_text/api/connect.py

from flask import Blueprint, request, jsonify
import os
import logging

connect_bp = Blueprint("connect", __name__)

@connect_bp.route("/copy", methods=["POST"])
def speech_to_clipboard():
    """
    Handle speech-to-clipboard requests.
    Expects JSON data with speech content.
    """
    if not request.is_json:
        return jsonify({
            "status": "error",
            "message": "Content-Type must be application/json"
        }), 400
    
    try:
        data = request.json
        
        # Validate required fields
        if "content" not in data:
            return jsonify({
                "status": "error",
                "message": "Missing required field: content"
            }), 400
            
        # TODO: Implement speech-to-clipboard logic
        # For now, just acknowledge receipt
        return jsonify({
            "status": "success",
            "message": "Speech content received",
            "data": {
                "content": data["content"]
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Error processing speech-to-clipboard request: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500

@connect_bp.route("/chat", methods=["POST"])
def speech_to_chat():
    """
    Handle speech-to-chat requests.
    Expects JSON data with speech content and optional chat parameters.
    """
    if not request.is_json:
        return jsonify({
            "status": "error",
            "message": "Content-Type must be application/json"
        }), 400
    
    try:
        data = request.json
        
        # Validate required fields
        if "content" not in data:
            return jsonify({
                "status": "error",
                "message": "Missing required field: content"
            }), 400
            
        # Optional chat parameters
        chat_id = data.get("chat_id")
        
        # TODO: Implement speech-to-chat logic
        # For now, just acknowledge receipt
        return jsonify({
            "status": "success",
            "message": "Chat content received",
            "data": {
                "content": data["content"],
                "chat_id": chat_id
            }
        }), 200
        
    except Exception as e:
        logging.error(f"Error processing speech-to-chat request: {str(e)}")
        return jsonify({
            "status": "error",
            "message": "Internal server error"
        }), 500