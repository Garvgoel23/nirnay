"""
SQLAlchemy ORM models for all Nirṇay database tables.
Insert-only tables (evaluation_verdicts, llm_audit_log, officer_actions) are never updated or deleted.
"""
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, Text, DateTime,
    ForeignKey, JSON, BigInteger
)
from sqlalchemy.orm import relationship
from db.database import Base


def generate_uuid():
    return str(uuid.uuid4())


def utcnow():
    return datetime.now(timezone.utc)


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=generate_uuid)
    tender_id = Column(String, nullable=False, index=True)
    bidder_id = Column(String, nullable=True)
    department_id = Column(String, nullable=False)
    doc_type = Column(String, nullable=False)  # tender | bidder
    original_filename = Column(String, nullable=False)
    storage_path = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="uploaded")
    # uploaded → ocr_processing → ocr_complete → extracting → extracted → error
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    pages = relationship("DocumentPage", back_populates="document", cascade="all, delete-orphan")
    authenticity = relationship("DocumentAuthenticity", back_populates="document", uselist=False)


class DocumentPage(Base):
    __tablename__ = "document_pages"

    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, index=True)
    page_num = Column(Integer, nullable=False)
    raw_text = Column(Text, nullable=False)
    extraction_method = Column(String, nullable=False)  # pdfminer | documentai | docx
    confidence_avg = Column(Float, nullable=True)
    word_count = Column(Integer, nullable=False, default=0)
    extracted_at = Column(DateTime, default=utcnow)

    document = relationship("Document", back_populates="pages")


class TenderCriterion(Base):
    __tablename__ = "tender_criteria"

    criterion_id = Column(String, primary_key=True)
    tender_id = Column(String, nullable=False, index=True)
    department_id = Column(String, nullable=False)
    type = Column(String, nullable=False)  # financial | technical | compliance | documentation
    description = Column(Text, nullable=False)
    threshold_value = Column(String, nullable=True)
    threshold_unit = Column(String, nullable=True)
    mandatory = Column(Boolean, nullable=False, default=True)
    raw_text_snippet = Column(Text, nullable=True)
    page_reference = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    extracted_values = relationship("BidderExtractedValue", back_populates="criterion")


class BidderExtractedValue(Base):
    __tablename__ = "bidder_extracted_values"

    value_id = Column(String, primary_key=True, default=generate_uuid)
    criterion_id = Column(String, ForeignKey("tender_criteria.criterion_id"), nullable=False, index=True)
    bidder_id = Column(String, nullable=False, index=True)
    tender_id = Column(String, nullable=False, index=True)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False)
    extracted_value = Column(String, nullable=True)
    value_unit = Column(String, nullable=True)
    confidence_score = Column(Float, nullable=False, default=0.0)
    source_page = Column(Integer, nullable=True)
    source_snippet = Column(Text, nullable=True)
    extraction_status = Column(String, nullable=False)
    # found_clear | found_ambiguous | not_found | contradicted
    extracted_at = Column(DateTime, default=utcnow)

    criterion = relationship("TenderCriterion", back_populates="extracted_values")


class DocumentAuthenticity(Base):
    __tablename__ = "document_authenticity"

    id = Column(String, primary_key=True, default=generate_uuid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, unique=True)
    authenticity_score = Column(Float, nullable=False)
    flags = Column(JSON, nullable=True)
    scored_at = Column(DateTime, default=utcnow)

    document = relationship("Document", back_populates="authenticity")


class TenderAnomaly(Base):
    __tablename__ = "tender_anomalies"

    id = Column(String, primary_key=True, default=generate_uuid)
    tender_id = Column(String, nullable=False, index=True)
    anomaly_type = Column(String, nullable=False)
    bidder_ids = Column(JSON, nullable=True)
    evidence = Column(JSON, nullable=True)
    severity = Column(String, nullable=False)
    detected_at = Column(DateTime, default=utcnow)


class TenderContradiction(Base):
    __tablename__ = "tender_contradictions"

    id = Column(String, primary_key=True, default=generate_uuid)
    tender_id = Column(String, nullable=False, index=True)
    criterion_ids = Column(JSON, nullable=True)
    description = Column(Text, nullable=False)
    contradiction_type = Column(String, nullable=False)
    # logical_impossibility | undefined_scope | ambiguous_threshold | circular_reference
    severity = Column(String, nullable=False)  # warning | error
    suggested_resolution = Column(Text, nullable=True)
    detected_at = Column(DateTime, default=utcnow)


class EvaluationVerdict(Base):
    """INSERT ONLY — never UPDATE or DELETE."""
    __tablename__ = "evaluation_verdicts"

    verdict_id = Column(String, primary_key=True, default=generate_uuid)
    tender_id = Column(String, nullable=False, index=True)
    bidder_id = Column(String, nullable=False, index=True)
    criterion_id = Column(String, ForeignKey("tender_criteria.criterion_id"), nullable=False)
    verdict = Column(String, nullable=False)  # ELIGIBLE | NOT_ELIGIBLE | MANUAL_REVIEW
    confidence_score = Column(Float, nullable=False)
    evidence_document_id = Column(String, nullable=True)
    source_page = Column(Integer, nullable=True)
    extracted_value = Column(String, nullable=True)
    threshold_value = Column(String, nullable=True)
    ambiguity_reason = Column(Text, nullable=True)
    reasoning_trace = Column(JSON, nullable=True)
    llm_model_used = Column(String, nullable=True)
    supersedes_verdict_id = Column(String, nullable=True)
    evaluated_at = Column(DateTime, default=utcnow)
    schema_version = Column(String, default="1.0")


class BidderOverallVerdict(Base):
    __tablename__ = "bidder_overall_verdicts"

    id = Column(String, primary_key=True, default=generate_uuid)
    tender_id = Column(String, nullable=False, index=True)
    bidder_id = Column(String, nullable=False, index=True)
    overall_verdict = Column(String, nullable=False)
    failing_criteria = Column(JSON, nullable=True)
    manual_review_criteria = Column(JSON, nullable=True)
    evaluated_at = Column(DateTime, default=utcnow)
    supersedes_id = Column(String, nullable=True)


class LLMAuditLog(Base):
    """INSERT ONLY — never UPDATE or DELETE."""
    __tablename__ = "llm_audit_log"

    id = Column(String, primary_key=True, default=generate_uuid)
    service = Column(String, nullable=False)
    model = Column(String, nullable=False)
    prompt_hash_sha256 = Column(String, nullable=False)
    response_hash_sha256 = Column(String, nullable=False)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    latency_ms = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=utcnow)


class OfficerAction(Base):
    """INSERT ONLY — never UPDATE or DELETE."""
    __tablename__ = "officer_actions"

    id = Column(String, primary_key=True, default=generate_uuid)
    officer_id = Column(String, nullable=False, index=True)
    officer_email = Column(String, nullable=False)
    action_type = Column(String, nullable=False)
    # override_verdict | sign_off | export_audit | export_report
    target_id = Column(String, nullable=False)
    comment = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=utcnow)


class PrecedentMemory(Base):
    __tablename__ = "precedent_memory"

    id = Column(String, primary_key=True, default=generate_uuid)
    department_id = Column(String, nullable=False, index=True)
    criterion_type = Column(String, nullable=False)
    criterion_description_embedding = Column(JSON, nullable=True)
    ambiguity_description = Column(Text, nullable=False)
    resolution = Column(Text, nullable=False)
    resolved_by_officer_id = Column(String, nullable=False)
    tender_id = Column(String, nullable=False)
    created_at = Column(DateTime, default=utcnow)
