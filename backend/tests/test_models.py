"""Tests for Pydantic model validators."""
import pytest
from pydantic import ValidationError


class TestEvaluationVerdictValidation:
    def test_manual_review_without_reason_raises(self):
        from models.verdict import EvaluationVerdictResponse
        with pytest.raises(ValidationError):
            EvaluationVerdictResponse(
                verdict_id="v1", tender_id="t1", bidder_id="b1",
                criterion_id="c1", verdict="MANUAL_REVIEW",
                confidence_score=0.5, ambiguity_reason=None
            )

    def test_manual_review_with_reason_passes(self):
        from models.verdict import EvaluationVerdictResponse
        v = EvaluationVerdictResponse(
            verdict_id="v1", tender_id="t1", bidder_id="b1",
            criterion_id="c1", verdict="MANUAL_REVIEW",
            confidence_score=0.5, ambiguity_reason="Low confidence extraction"
        )
        assert v.verdict == "MANUAL_REVIEW"

    def test_eligible_without_reason_passes(self):
        from models.verdict import EvaluationVerdictResponse
        v = EvaluationVerdictResponse(
            verdict_id="v1", tender_id="t1", bidder_id="b1",
            criterion_id="c1", verdict="ELIGIBLE",
            confidence_score=0.9
        )
        assert v.verdict == "ELIGIBLE"


class TestOfficerActionValidation:
    def test_comment_below_20_chars_raises(self):
        from models.verdict import OverrideRequest
        with pytest.raises(ValidationError):
            OverrideRequest(new_verdict="ELIGIBLE", comment="too short")

    def test_comment_exactly_20_chars_passes(self):
        from models.verdict import OverrideRequest
        r = OverrideRequest(new_verdict="ELIGIBLE", comment="A" * 20)
        assert len(r.comment) == 20

    def test_invalid_verdict_raises(self):
        from models.verdict import OverrideRequest
        with pytest.raises(ValidationError):
            OverrideRequest(new_verdict="INVALID", comment="A" * 20)


class TestExtractedValueValidation:
    def test_confidence_above_1_raises(self):
        from models.bidder import ExtractedValue
        with pytest.raises(ValidationError):
            ExtractedValue(
                criterion_id="c1", bidder_id="b1", tender_id="t1",
                document_id="d1", confidence_score=1.1,
                extraction_status="found_clear"
            )

    def test_confidence_negative_raises(self):
        from models.bidder import ExtractedValue
        with pytest.raises(ValidationError):
            ExtractedValue(
                criterion_id="c1", bidder_id="b1", tender_id="t1",
                document_id="d1", confidence_score=-0.1,
                extraction_status="found_clear"
            )

    def test_valid_confidence_passes(self):
        from models.bidder import ExtractedValue
        v = ExtractedValue(
            criterion_id="c1", bidder_id="b1", tender_id="t1",
            document_id="d1", confidence_score=0.85,
            extraction_status="found_clear"
        )
        assert v.confidence_score == 0.85
