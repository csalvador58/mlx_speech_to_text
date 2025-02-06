# File: src/speech_to_text/utils/path_utils.py
"""
Path handling utilities for the speech-to-text application.
Provides consistent path operations and validation across the application.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Union, List, Pattern
import re


def normalize_path(path: Union[str, Path]) -> Path:
    """
    Normalize a path string or Path object to an absolute Path.
    Handles home directory expansion and path resolution.

    Args:
        path: Path string or Path object to normalize

    Returns:
        Path: Normalized absolute Path object
    """
    if isinstance(path, str):
        path = Path(path)
    return path.expanduser().resolve()


def ensure_directory(directory: Union[str, Path]) -> bool:
    """
    Ensure a directory exists and is writable.

    Args:
        directory: Directory path to verify/create

    Returns:
        bool: True if directory exists and is writable
    """
    try:
        dir_path = normalize_path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)

        # Test write permissions with a temporary file
        test_file = dir_path / ".write_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
            
            return True
        except Exception as e:
            logging.error(f"Directory is not writable: {dir_path} - {e}")
            return False
    except Exception as e:
        logging.error(f"Error creating/verifying directory: {directory} - {e}")
        return False


def validate_file_path(
    file_path: Union[str, Path],
    must_exist: bool = False,
    file_type: Optional[str] = None,
) -> Optional[Path]:
    """
    Validate a file path and ensure its directory exists.

    Args:
        file_path: Path to validate
        must_exist: Whether the file must already exist
        file_type: Optional file extension to validate (e.g., '.txt')

    Returns:
        Optional[Path]: Validated Path object or None if validation fails
    """
    try:
        path = normalize_path(file_path)

        # Validate file type if specified
        if file_type and path.suffix.lower() != file_type.lower():
            logging.error(f"Invalid file type: {path.suffix}. Expected: {file_type}")
            return None

        # Check existence if required
        if must_exist and not path.exists():
            logging.error(f"File not found: {path}")
            return None

        # Ensure parent directory exists and is writable
        if not ensure_directory(path.parent):
            return None

        return path

    except Exception as e:
        logging.error(f"Error validating file path: {file_path} - {e}")
        return None


def safe_read_file(
    file_path: Union[str, Path], encoding: str = "utf-8"
) -> Optional[str]:
    """
    Safely read a file with proper path handling.

    Args:
        file_path: Path to file to read
        encoding: File encoding to use

    Returns:
        Optional[str]: File contents if successful, None otherwise
    """
    try:
        path = validate_file_path(file_path, must_exist=True)
        if not path:
            return None

        content = path.read_text(encoding=encoding)
        if not content.strip():
            logging.error("File is empty")
            return None

        return content

    except Exception as e:
        logging.error(f"Error reading file: {file_path} - {e}")
        return None


def safe_write_file(
    content: str,
    file_path: Union[str, Path],
    encoding: str = "utf-8",
    append: bool = False,
) -> bool:
    """
    Safely write content to a file with proper path handling.

    Args:
        content: Content to write
        file_path: Path to write to
        encoding: File encoding to use
        append: Whether to append to existing file

    Returns:
        bool: True if write was successful
    """
    try:
        path = validate_file_path(file_path)
        if not path:
            return False

        mode = "a" if append else "w"
        path.write_text(content, encoding=encoding)
        logging.debug(f"Successfully wrote to file: {path}")
        return True

    except Exception as e:
        logging.error(f"Error writing to file: {file_path} - {e}")
        return False


def safe_list_files(directory: Union[str, Path], extension: str = ".json") -> List[Path]:
    """
    Safely list files in a directory with specific extension.

    Args:
        directory: Directory to list files from
        extension: File extension to filter (default: .json)

    Returns:
        List[Path]: List of matching file paths, empty list if directory invalid
    """
    try:
        dir_path = normalize_path(directory)
        if not dir_path.exists() or not dir_path.is_dir():
            logging.warning(f"Directory does not exist or is not a directory: {directory}")
            return []

        # Get all files with specified extension
        files = list(dir_path.glob(f"*{extension}"))
        
        logging.debug(f"Found {len(files)} {extension} files in {dir_path}")
        return sorted(files)

    except Exception as e:
        logging.error(f"Error listing directory contents: {directory} - {e}")
        return []