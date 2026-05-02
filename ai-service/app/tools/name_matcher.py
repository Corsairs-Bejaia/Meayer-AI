import difflib
import re
import logging
from typing import List, Optional, Tuple

try:
    import pyarabic.araby as araby
    _HAS_PYARABIC = True
except ImportError:
    _HAS_PYARABIC = False

try:
    from unidecode import unidecode
    _HAS_UNIDECODE = True
except ImportError:
    _HAS_UNIDECODE = False

logger = logging.getLogger(__name__)

_TITLES = re.compile(
    ,
    re.IGNORECASE,
)
_ARABIC_SCRIPT = re.compile(r"[\u0600-\u06FF]")


_PREFIX_MAP = {
    : "ben", "bel": "bel", "bou": "bou",
    : "abd", "abde": "abd", "abdel": "abd",
    : "el", "al": "el",
}


def _normalize_french(name: str) -> str:
    name = name.strip()
    name = _TITLES.sub("", name)
    if _HAS_UNIDECODE:
        name = unidecode(name)
    name = re.sub(r"[^a-zA-Z\s'-]", " ", name)
    name = re.sub(r"[-_]", " ", name)
    name = name.lower()
    
    for prefix in ["ben", "bou", "bel", "abd", "el", "al"]:
        name = re.sub(rf"\b{prefix}\s+", prefix, name)
    name = re.sub(r"\s+", " ", name).strip()
    return name


def _normalize_arabic(name: str) -> str:
    name = name.strip()
    if not _HAS_PYARABIC:
        return name
    name = araby.strip_tashkeel(name)
    name = araby.strip_tatweel(name)
    name = araby.normalize_alef(name)
    name = araby.normalize_hamza(name)
    name = name.replace("ة", "ه")
    name = re.sub(r"\s+", " ", name).strip()
    return name


def _is_arabic(text: str) -> bool:
    return bool(_ARABIC_SCRIPT.search(text))


def _token_set_ratio(a: str, b: str) -> float:
    
    tokens_a = set(a.split())
    tokens_b = set(b.split())
    intersection = tokens_a & tokens_b
    remainder_a = tokens_a - intersection
    remainder_b = tokens_b - intersection

    sorted_intersection = " ".join(sorted(intersection))
    sorted_a = sorted_intersection + " " + " ".join(sorted(remainder_a))
    sorted_b = sorted_intersection + " " + " ".join(sorted(remainder_b))

    ratios = [
        difflib.SequenceMatcher(None, sorted_intersection.strip(), sorted_a.strip()).ratio(),
        difflib.SequenceMatcher(None, sorted_intersection.strip(), sorted_b.strip()).ratio(),
        difflib.SequenceMatcher(None, sorted_a.strip(), sorted_b.strip()).ratio(),
    ]
    return max(ratios)


class NameMatcher:
    

    MATCH_THRESHOLD = 0.75

    @staticmethod
    def normalize(name: str) -> str:
        if _is_arabic(name):
            return _normalize_arabic(name)
        return _normalize_french(name)

    @staticmethod
    def match_names(name_a: str, name_b: str) -> Tuple[bool, float]:
        if not name_a or not name_b:
            return False, 0.0

        norm_a = NameMatcher.normalize(name_a)
        norm_b = NameMatcher.normalize(name_b)

        
        direct = _token_set_ratio(norm_a, norm_b)

        
        cross = 0.0
        if _is_arabic(name_a) != _is_arabic(name_b):
            
            if _is_arabic(name_a) and _HAS_UNIDECODE:
                lat_a = unidecode(norm_a)
                cross = _token_set_ratio(lat_a, norm_b)
            elif _is_arabic(name_b) and _HAS_UNIDECODE:
                lat_b = unidecode(norm_b)
                cross = _token_set_ratio(norm_a, lat_b)

        score = max(direct, cross)
        return score >= NameMatcher.MATCH_THRESHOLD, round(score, 3)

    @staticmethod
    def compare_all_name_pairs(names: List[str]) -> Tuple[bool, float]:
        if len(names) < 2:
            return True, 1.0

        scores = []
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                _, score = NameMatcher.match_names(names[i], names[j])
                scores.append(score)

        avg = sum(scores) / len(scores)
        return avg >= NameMatcher.MATCH_THRESHOLD, round(avg, 3)
