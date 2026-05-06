"""Pydantic models for tender-related data structures."""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ExtractedCriterion(BaseModel):
    criterion_id: Optional[str] = None
    type: str = Field(..., pattern=r"^(financial|technical|compliance|documentation)$")
    description: str
    threshold_value: Optional[str] = None
    threshold_unit: Optional[str] = None
    mandatory: bool = True
    raw_text_snippet: Optional[str] = None
    page_reference: Optional[int] = None


class TenderContradictionResponse(BaseModel):
    contradiction_id: Optional[str] = None
    criterion_ids: List[str]
    description: str
    contradiction_type: str = Field(
        ...,
        pattern=r"^(logical_impossibility|undefined_scope|ambiguous_threshold|circular_reference)$"
    )
    severity: str = Field(..., pattern=r"^(warning|error)$")
    suggested_resolution: Optional[str] = None


class TenderAnomalyResponse(BaseModel):
    id: Optional[str] = None
    tender_id: str
    anomaly_type: str
    bidder_ids: List[str]
    evidence: dict
    severity: str
    detected_at: Optional[datetime] = None


class CriteriaListResponse(BaseModel):
    criteria: List[ExtractedCriterion]
    tender_id: str
    total_count: int


class ContradictionListResponse(BaseModel):
    contradictions: List[TenderContradictionResponse]
    tender_id: str
    total_count: int
