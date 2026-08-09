import re
from typing import List, Optional

def clean_stutters(text: str) -> str:
    """Removes repeated adjacent words or phrases caused by small model generation artifacts."""
    if not text:
        return text

    # Remove duplicated single words: e.g. "for for" -> "for", "the the" -> "the"
    cleaned = re.sub(r'\b(\w+)\s+\1\b', r'\1', text, flags=re.IGNORECASE)
    
    # Remove doubled word roots/prefixes: e.g. "forfor" -> "for"
    cleaned = re.sub(r'\b(for|the|and|in|to|of|that|with|on|at|is|it)\1\b', r'\1', cleaned, flags=re.IGNORECASE)

    # Remove repeated adjacent sentences or phrases
    cleaned = re.sub(r'([^.!?]+[.!?])\s*\1', r'\1', cleaned)
    
    # Clean up awkward formatting
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    
    return cleaned


def fix_name_references(text: str, canonical_names: List[str]) -> str:
    """Corrects mangled names in model speech back to canonical panelist names."""
    if not text or not canonical_names:
        return text

    cleaned = text
    for name in canonical_names:
        first_name = name.split()[0]
        last_name = name.split()[-1] if len(name.split()) > 1 else ""
        
        # Common mangled patterns for names like "Dr. Aris Vance" -> "Dr. Arvane", "Dr. Arv", "Arv Vance"
        if len(first_name) >= 3 and len(last_name) >= 3:
            mangled_pattern = r'\b(Dr\.\s*)?' + re.escape(first_name[:3]) + r'\w*' + re.escape(last_name[-3:]) + r'\b'
            cleaned = re.sub(mangled_pattern, name, cleaned, flags=re.IGNORECASE)

    return cleaned


GENERIC_RESPONSE_PATTERNS = [
    r"i agree we must carefully examine",
    r"reflecting on current dialogue",
    r"delivering response to panel",
    r"engaging in socratic debate",
    r"reasoning for action",
    r"worth warrant further discussion",
]

def is_generic_response(text: str) -> bool:
    """Detects if a generated speech message is a low-quality fallback or generic phrase."""
    if not text or len(text.strip()) < 30:
        return True
    
    lower = text.lower()
    for pattern in GENERIC_RESPONSE_PATTERNS:
        if re.search(pattern, lower):
            return True
            
    return False
