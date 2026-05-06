"""Pydantic models for verdict-related data structures."""
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class VerdictOutcome(BaseModel):
    verdict: str = Field(..., pattern=r"^(ELIGIBLE|NOT_ELIGIBLE|MANUAL_REVIEW)$")
    confidence: float = Field(..., ge=0.0, le=1.0)
    reasoning: Optional[str] = None
    reasoning_trace: Optional[Dict[str, Any]] = None


class EvaluationVerdictResponse(BaseModel):
    verdict_id: str
    tender_id: str
    bidder_id: str
    criterion_id: str
    verdict: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    evidence_document_id: Optional[str] = None
    source_page: Optional[int] = None
    extracted_value: Optional[str] = None
    threshold_value: Optional[str] = None
    ambiguity_reason: Optional[str] = None
    reasoning_trace: Optional[Dict[str, Any]] = None
    llm_model_used: Optional[str] = None
    supersedes_verdict_id: Optional[str] = None
    evaluated_at: Optional[datetime] = None
    schema_version: str = "1.0"

    @model_validator(mode="after")
    def validate_ambiguity_reason(self):
        if self.verdict == "MANUAL_REVIEW" and not self.ambiguity_reason:
            raise ValueError("ambiguity_reason is required when verdict is MANUAL_REVIEW")
        return self


class BidderOverallVerdictResponse(BaseModel):
    id: str
    tender_id: str
    bidder_id: str
    overall_verdict: str
    failing_criteria: Optional[List[str]] = None
    manual_review_criteria: Optional[List[str]] = None
    evaluated_at: Optional[datetime] = None


class BidderVerdictGroup(BaseModel):
    bidder_id: str
    overall_verdict: str
    criteria_verdicts: List[EvaluationVerdictResponse]
    failing_criteria: Optional[List[str]] = None
    manual_review_criteria: Optional[List[str]] = None


class TenderResultsResponse(BaseModel):
    tender_id: str
    bidders: List[BidderVerdictGroup]
    total_bidders: int
    total_criteria: int


class EvaluationStatusResponse(BaseModel):
    tender_id: str
    processed: int
    total: int
    status: str  # processing | complete


class OverrideRequest(BaseModel):
    new_verdict: str = Field(..., pattern=r"^(ELIGIBLE|NOT_ELIGIBLE)$")
    comment: str = Field(..., min_length=20)
