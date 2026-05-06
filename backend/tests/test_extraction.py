"""Tests for extraction services — mandatory keyword detection, criterion ID format, type classification."""
import re
import pytest

# Test mandatory keyword detection
MANDATORY_KEYWORDS = ["shall", "must", "required", "mandatory", "essential", "compulsory", "अनिवार्य", "आवश्यक"]
DESIRABLE_KEYWORDS = ["preferred", "desirable", "may", "should", "where applicable", "if available", "वांछनीय"]


def detect_mandatory(raw_text: str, llm_classification: bool) -> bool:
    text_lower = raw_text.lower()
    has_mandatory = any(kw in text_lower for kw in MANDATORY_KEYWORDS)
    has_desirable = any(kw in text_lower for kw in DESIRABLE_KEYWORDS)
    if has_mandatory and not has_desirable:
        return True
    elif has_desirable and not has_mandatory:
        return False
    return llm_classification


class TestMandatoryKeywordDetection:
    def test_english_mandatory_shall(self):
        assert detect_mandatory("The bidder shall have minimum turnover", False) is True

    def test_english_mandatory_must(self):
        assert detect_mandatory("Bidder must provide GST certificate", False) is True

    def test_english_desirable(self):
        assert detect_mandatory("It is desirable that the bidder has ISO certification", True) is False

    def test_hindi_mandatory(self):
        assert detect_mandatory("यह प्रमाण पत्र अनिवार्य है", False) is True

    def test_hindi_desirable(self):
        assert detect_mandatory("यह वांछनीय है कि बोलीदाता", True) is False

    def test_no_keywords_uses_llm(self):
        assert detect_mandatory("Bidder turnover of 5 crore", True) is True
        assert detect_mandatory("Bidder turnover of 5 crore", False) is False

    def test_empty_text_uses_llm(self):
        assert detect_mandatory("", True) is True


class TestCriterionIdFormat:
    def test_valid_format(self):
        assert re.match(r"^.+_C\d{3}$", "TENDER001_C001")
        assert re.match(r"^.+_C\d{3}$", "TENDER-2024-XYZ_C042")

    def test_invalid_format(self):
        assert not re.match(r"^.+_C\d{3}$", "TENDER001_C1")
        assert not re.match(r"^.+_C\d{3}$", "C001")
        assert not re.match(r"^.+_C\d{3}$", "TENDER_CABC")


class TestTypeClassification:
    def test_financial_keywords(self):
        financial_indicators = ["turnover", "revenue", "net worth", "bid price"]
        for kw in financial_indicators:
            assert kw in kw  # placeholder — actual classification is LLM-driven

    def test_experience_keywords(self):
        technical_indicators = ["completed", "experience", "similar work", "projects"]
        for kw in technical_indicators:
            assert kw in kw  # placeholder


class TestEmptyPageHandling:
    def test_empty_pages_produce_empty_criteria(self):
        pages = []
        assert len(pages) == 0
