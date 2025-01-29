# File: src/speech_to_text/config/text_optimizations.py
"""
Configuration file containing text optimization rules for voice synthesis.
These rules are used to enhance the quality of synthesized speech output.
"""
import re

# Word replacements for common abbreviations and terms
# Keys are matched case-insensitively
WORD_REPLACEMENTS = {
    # Technical terms
    "jsonl": "json el",
    "api": "A P I",
    "url": "U R L",
    "sql": "S Q L",
    "html": "H T M L",
    "css": "C S S",
    "js": "JavaScript",
    "jwt": "J W T",
    "crud": "C R U D",
    "ui": "U I",
    "ux": "U X",
    "cdn": "C D N",
    "ssl": "S S L",
    "tcp": "T C P",
    "ip": "I P",
    
    # Numbers in lists
    r"^\d+\.": "",  # Remove numbered list markers
    
    # Common markdown patterns
    r"\*\*(.+?)\*\*": r"\1",  # Remove bold markers
    r"\*(.+?)\*": r"\1",      # Remove italic markers
    r"_(.+?)_": r"\1",        # Remove underscore emphasis
    r"`(.+?)`": r"\1",        # Remove code markers
    r"#": "",                 # Remove header markers
    r"\[(.+?)\](\(.+?\))": r"\1",  # Convert links to just text
}

# Punctuation replacements for better speech pacing
# Applied only when characters are surrounded by spaces or at string boundaries
PUNCTUATION_REPLACEMENTS = {
    ".": "...",     # Extend pause at sentence end
    ":": ",",       # Convert colons to commas for more natural pausing
    "–": " ",       # Convert en-dash to space
    "—": " ",       # Convert em-dash to space
    ";": ",",       # Convert semicolons to commas
    "•": ", ",      # Convert bullets to comma and space
    ">": ", ",      # Convert blockquote markers to pauses
}

# Global character replacements
# Applied to all occurrences regardless of surrounding context
GLOBAL_REPLACEMENTS = {
    "#": "",        # Remove hashtags
    "*": "",        # Remove asterisks
    "-": " ",       # Convert hyphens to spaces
    "–": "",        # Remove en-dashes
    "—": "",        # Remove em-dashes
    "`": "",        # Remove backticks
    "|": "",        # Remove vertical bars
    "~": "",        # Remove tildes
    "•": ",",       # Convert bullets to commas
    "_": "",        # Remove underscores
    "[": "",        # Remove square brackets
    "]": "",        # Remove square brackets
    "(": "",        # Remove parentheses
    ")": "",        # Remove parentheses
}

# Pre-processing patterns for specific formats
LIST_ITEM_PATTERN = re.compile(r'^\d+\.\s+')
MARKDOWN_BOLD_PATTERN = re.compile(r'\*\*(.+?)\*\*')
MARKDOWN_ITALIC_PATTERN = re.compile(r'\*(.+?)\*')
MARKDOWN_LINK_PATTERN = re.compile(r'\[(.+?)\]\(.+?\)')
MARKDOWN_CODE_PATTERN = re.compile(r'`(.+?)`')