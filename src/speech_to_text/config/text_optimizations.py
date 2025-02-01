# File: src/speech_to_text/config/text_optimizations.py
"""
Configuration file containing text optimization rules for voice synthesis.
These rules are used to enhance the quality of synthesized speech output.
"""
from dataclasses import dataclass, field
from typing import Dict
import re

def get_default_abbreviations() -> Dict[str, str]:
    return {
        # "api": "A P I",
        "e.g.": "example given",
        "i.e.": "in example",
        "url": "U R L",
        "sql": "S Q L",
        "html": "H T M L",
        "css": "C S S",
        "js": "JavaScript",
        "jwt": "J W T",
        "crud": "C R U D",
        "ui": "U I",
        "ux": "U X",
    }

def get_default_char_replacements() -> Dict[str, str]:
    return {
        "<|START_RESPONSE|>": "",  # Manually remove tokens
        "<|END_RESPONSE|>": "",
        ".": "...",  # Extend pause
        ":": ",",    # Natural pause
        ";": ",",    # Natural pause
        "–": " ",    # Space for readability
        "—": " ",    # Space for readability
        "|": ",",    # Natural pause
        "•": ",",    # Natural pause for bullets
    }

def get_default_pronunciations() -> Dict[str, str]:
    return {
        "pikachu": "peeka-chu",
    }

@dataclass
class TextOptimizer:
    """
    Handles text optimization for voice synthesis with clear separation of concerns.
    """
    ABBREVIATIONS: Dict[str, str] = field(default_factory=get_default_abbreviations)
    CHAR_REPLACEMENTS: Dict[str, str] = field(default_factory=get_default_char_replacements)
    PRONUNCIATIONS: Dict[str, str] = field(default_factory=get_default_pronunciations)
    CHARS_TO_REMOVE: str = r'[*#`~\[\]()]'

    def optimize(self, text: str) -> str:
        """
        Optimize text for voice synthesis using a clear, sequential process.
        
        Args:
            text: Input text to optimize
            
        Returns:
            str: Optimized text for voice synthesis
        """
        if not text:
            return text

        # 1. Replace abbreviations (case-insensitive)
        pattern = r'\b(' + '|'.join(map(re.escape, self.ABBREVIATIONS.keys())) + r')\b'
        text = re.sub(pattern, lambda m: self.ABBREVIATIONS[m.group().lower()], text, flags=re.IGNORECASE)

        # 2. Replace characters for better speech flow
        for char, replacement in self.CHAR_REPLACEMENTS.items():
            text = text.replace(char, replacement)

        # 3. Remove unnecessary characters
        text = re.sub(self.CHARS_TO_REMOVE, ' ', text)

        # 4. Clean up whitespace and add natural pauses
        text = ' '.join(text.split())  # Normalize spaces
        text = re.sub(r'(?<=\w)\.(?=\s+[A-Z])', '... ', text)  # Add pauses between sentences

        # 5. Apply pronunciation optimizations (done last to preserve special characters)
        pattern = r'\b(' + '|'.join(map(re.escape, self.PRONUNCIATIONS.keys())) + r')\b'
        text = re.sub(pattern, lambda m: self.PRONUNCIATIONS[m.group().lower()], text, flags=re.IGNORECASE)

        return text

    def __call__(self, text: str) -> str:
        """
        Make the class callable for easier integration.
        
        Args:
            text: Input text to optimize
            
        Returns:
            str: Optimized text
        """
        return self.optimize(text)

# Create a singleton instance
optimizer = TextOptimizer()