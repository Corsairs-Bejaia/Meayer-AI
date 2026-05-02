import unicodedata
import pyarabic.araby as araby
from unidecode import unidecode
from typing import Tuple
import logging

logger = logging.getLogger(__name__)

class NameMatcher:
    """
    Tool for matching Arabic and French names across documents.
    """
    
    @staticmethod
    def normalize_french(name: str) -> str:
        if not name:
            return ""
        # Lowercase and remove diacritics
        name = name.lower()
        name = unidecode(name)
        # Remove common titles
        titles = ["dr", "m.", "mme", "mlle", "pr"]
        words = name.split()
        words = [w for w in words if w.replace(".", "") not in titles]
        return " ".join(words).strip()

    @staticmethod
    def normalize_arabic(name: str) -> str:
        if not name:
            return ""
        # Remove tashkeel and normalize alef/taa marbuta
        name = araby.strip_tashkeel(name)
        name = araby.strip_tatweel(name)
        name = araby.normalize_alef(name)
        name = araby.normalize_hamza(name)
        # Custom normalization for common variations
        name = name.replace("ة", "ه")
        return name.strip()

    @staticmethod
    def transliterate_ar_to_fr(name_ar: str) -> str:
        """
        Simple rule-based transliteration for Algerian names.
        """
        # This is a complex mapping, using a simplified version for now
        mapping = {
            'خ': 'kh', 'ش': 'ch', 'ع': 'a', 'غ': 'gh', 'ق': 'k', 'ج': 'dj',
            'ح': 'h', 'ص': 's', 'ض': 'd', 'ط': 't', 'ظ': 'z', 'ث': 'th',
            'ذ': 'dh'
        }
        # In practice, we might use a library or LLM for better results
        # For now, we'll rely more on fuzzy matching and script detection
        return name_ar # Placeholder

    @staticmethod
    def fuzzy_match(s1: str, s2: str) -> float:
        """
        Simple Levenshtein similarity.
        """
        import difflib
        return difflib.SequenceMatcher(None, s1, s2).ratio()

    @staticmethod
    def match_names(name_a: str, name_b: str) -> Tuple[bool, float]:
        """
        Matches two names, potentially in different scripts.
        """
        norm_a_fr = NameMatcher.normalize_french(name_a)
        norm_b_fr = NameMatcher.normalize_french(name_b)
        
        # If both look like French/Latin script
        if norm_a_fr and norm_b_fr:
            score = NameMatcher.fuzzy_match(norm_a_fr, norm_b_fr)
            return score >= 0.75, score
            
        # Handle Arabic cases (omitted for brevity in this step, but structure is there)
        return False, 0.0
