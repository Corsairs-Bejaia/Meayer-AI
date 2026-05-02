import pytest
from app.tools.name_matcher import NameMatcher


class TestNormalizeFrench:
    def test_strips_titles(self):
        from app.tools.name_matcher import _normalize_french
        assert "dupont" in _normalize_french("Dr. Dupont")
        assert "marie" in _normalize_french("Mme. Marie")

    def test_handles_diacritics(self):
        from app.tools.name_matcher import _normalize_french
        result = _normalize_french("Élodie Ômar")
        assert "elodie" in result
        assert "omar" in result

    def test_normalizes_hyphens(self):
        from app.tools.name_matcher import _normalize_french
        result = _normalize_french("Jean-Pierre")
        assert "jean pierre" in result


class TestMatchNames:
    
    def test_exact_match(self):
        matched, score = NameMatcher.match_names("Ahmed Benali", "Ahmed Benali")
        assert matched
        assert score > 0.95

    
    def test_case_insensitive(self):
        matched, score = NameMatcher.match_names("AHMED BENALI", "ahmed benali")
        assert matched

    
    def test_word_order_swap(self):
        matched, score = NameMatcher.match_names("Benali Ahmed", "Ahmed Benali")
        assert matched, f"Expected match but got score={score}"

    
    def test_ben_vs_beni(self):
        matched, score = NameMatcher.match_names("Ben Ali", "Benali")
        
        assert score > 0.5

    def test_spelling_variant_mohamed(self):
        matched, score = NameMatcher.match_names("Mohamed Saidi", "Mohammed Saidi")
        assert score > 0.8

    
    def test_different_names_no_match(self):
        matched, score = NameMatcher.match_names("Karim Ziani", "Farid Boudjenah")
        assert not matched
        assert score < 0.6

    
    def test_empty_name_a(self):
        matched, score = NameMatcher.match_names("", "Ahmed")
        assert not matched
        assert score == 0.0

    def test_empty_both(self):
        matched, score = NameMatcher.match_names("", "")
        assert not matched


class TestCompareAllPairs:
    def test_single_name_always_consistent(self):
        matched, score = NameMatcher.compare_all_name_pairs(["Ahmed Benali"])
        assert matched
        assert score == 1.0

    def test_two_matching_names(self):
        matched, score = NameMatcher.compare_all_name_pairs([
            , "ahmed benali"
        ])
        assert matched

    def test_three_consistent_names(self):
        matched, score = NameMatcher.compare_all_name_pairs([
            , "Fatima Z Ait", "Fatima Zohra AIT"
        ])
        assert score > 0.6  

    def test_mismatch_among_names(self):
        matched, score = NameMatcher.compare_all_name_pairs([
            , "Karim Ziani", "Ahmed Benali"
        ])
        assert not matched  
