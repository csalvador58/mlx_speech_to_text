# File: src/speech_to_text/llm/file_handler.py
"""
File handler for processing different document types.
Supports text files, PDFs, and images for LLM processing.
"""

import logging
import base64
import mimetypes
from pathlib import Path
from typing import Optional, Dict, Any, Union, Tuple
from PIL import Image
import pymupdf4llm

def get_file_type(file_path: Union[str, Path]) -> Optional[str]:
    """
    Determine file type from path.
    
    Args:
        file_path: Path to file
        
    Returns:
        Optional[str]: MIME type of file or None if unknown
    """
    try:
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            return mime_type
        return None
    except Exception as e:
        logging.error(f"Error determining file type: {e}")
        return None

def process_text_file(file_path: Union[str, Path]) -> Optional[str]:
    """
    Process text files (txt, md, etc).
    
    Args:
        file_path: Path to text file
        
    Returns:
        Optional[str]: File contents or None if error
    """
    try:
        content = Path(file_path).read_text(encoding='utf-8')
        return f"[File Type: Text Document]\n\n{content}"
    except Exception as e:
        logging.error(f"Error reading text file: {e}")
        return None

def process_pdf_file(file_path: Union[str, Path]) -> Optional[str]:
    """
    Convert PDF to markdown text.
    
    Args:
        file_path: Path to PDF file
        
    Returns:
        Optional[str]: Markdown text or None if error
    """
    try:
        markdown_text = pymupdf4llm.to_markdown(str(file_path))
        return f"[File Type: PDF Document]\n\n{markdown_text}"
    except Exception as e:
        logging.error(f"Error converting PDF: {e}")
        return None

def process_image_file(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """
    Process image files to base64.
    
    Args:
        file_path: Path to image file
        
    Returns:
        Optional[Dict]: Image content object for LLM API or None if error
    """
    try:
        # Open and verify image
        with Image.open(file_path) as img:
            # Convert to RGB if needed
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            # Get image format
            img_format = img.format or 'JPEG'
            
            # Save to bytes
            import io
            img_byte_arr = io.BytesIO()
            img.save(img_byte_arr, format=img_format)
            img_byte_arr = img_byte_arr.getvalue()
            
            # Convert to base64
            base64_img = base64.b64encode(img_byte_arr).decode('utf-8')
            
            # Create content object for API
            return {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/{img_format.lower()};base64,{base64_img}"
                }
            }
    except Exception as e:
        logging.error(f"Error processing image file: {e}")
        return None

def process_file(file_path: Union[str, Path]) -> Tuple[Optional[Union[str, Dict]], bool]:
    """
    Process file based on its type.
    
    Args:
        file_path: Path to file
        
    Returns:
        Tuple[Optional[Union[str, Dict]], bool]: 
            - Processed content or None if error
            - Boolean indicating if content is an image
    """
    try:
        mime_type = get_file_type(file_path)
        if not mime_type:
            logging.error(f"Unknown file type: {file_path}")
            return None, False
            
        # Process based on MIME type
        if mime_type.startswith('text/'):
            content = process_text_file(file_path)
            return content, False
            
        elif mime_type == 'application/pdf':
            content = process_pdf_file(file_path)
            return content, False
            
        elif mime_type.startswith('image/'):
            content = process_image_file(file_path)
            return content, True
            
        else:
            logging.error(f"Unsupported file type {mime_type}: {file_path}")
            return None, False
            
    except Exception as e:
        logging.error(f"Error processing file {file_path}: {e}")
        return None, False

def prepare_content_message(content: Union[str, Dict], is_image: bool) -> Dict[str, Any]:
    """
    Prepare content for LLM API message format.
    
    Args:
        content: Processed file content
        is_image: Whether content is an image
        
    Returns:
        Dict[str, Any]: Formatted message for LLM API
    """
    if is_image:
        return {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "Please analyze this image."
                },
                content  # Image content object
            ]
        }
    else:
        return {
            "role": "user",
            "content": content
        }