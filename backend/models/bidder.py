"""Pydantic models for bidder-related data structures."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class PageContent(BaseModel):
    page_num: int
    raw_text: str
    word_count: int = 0
    extraction_method: str = "pdfminer"
    needs_documentai: bool = False
    confidence_avg: Optional[float] = None


class ExtractedValue(BaseModel):
    value_id: Optional[str] = None
    criterion_id: str
    bidder_id: str
    tender_id: str
    document_id: str
    extracted_value: Optional[str] = None
    value_unit: Optional[str] = None
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    source_page: Optional[int] = None
    source_snippet: Optional[str] = None
    extraction_status: str = Field(
        ...,
        pattern=r"^(found_clear|found_ambiguous|not_found|contradicted|inferred)$"
    )
    extracted_at: Optional[datetime] = None


class DocumentUploadResponse(BaseModel):
    doc_id: str
    status: str = "accepted"


class DocumentStatusResponse(BaseModel):
    doc_id: str
    tender_id: str
    bidder_id: Optional[str] = None
    doc_type: str
    status: str
    error_message: Optional[str] = None
    original_filename: str
