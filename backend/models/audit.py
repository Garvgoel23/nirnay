"""Pydantic models for audit-related data structures."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class LLMAuditEntry(BaseModel):
    id: Optional[str] = None
    service: str
    model: str
    prompt_hash_sha256: str
    response_hash_sha256: str
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    latency_ms: Optional[float] = None
    timestamp: Optional[datetime] = None


class OfficerActionRequest(BaseModel):
    action_type: str = Field(
        ...,
        pattern=r"^(override_verdict|sign_off|export_audit|export_report)$"
    )
    target_id: str
    comment: Optional[str] = Field(None, min_length=20)


class OfficerActionResponse(BaseModel):
    id: str
    officer_id: str
    officer_email: str
    action_type: str
    target_id: str
    comment: Optional[str] = None
    timestamp: Optional[datetime] = None


class DashboardSummaryResponse(BaseModel):
    active_tenders: int
    pending_review_count: int
    recent_activity: list
