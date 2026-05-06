"""
Extraction router — criteria listing and re-extraction endpoints.
"""
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import TenderCriterion, Document, OfficerAction

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/extraction", tags=["Extraction"])


@router.get("/criteria/{tender_id}")
async def get_criteria(tender_id: str, db: Session = Depends(get_db)):
    """Get all extracted criteria for a tender, ordered by type then mandatory."""
    criteria = db.query(TenderCriterion).filter(
        TenderCriterion.tender_id == tender_id
    ).order_by(TenderCriterion.type, TenderCriterion.mandatory.desc()).all()

    return {
        "tender_id": tender_id,
        "total_count": len(criteria),
        "criteria": [
            {
                "criterion_id": c.criterion_id,
                "type": c.type,
                "description": c.description,
                "threshold_value": c.threshold_value,
                "threshold_unit": c.threshold_unit,
                "mandatory": c.mandatory,
                "raw_text_snippet": c.raw_text_snippet,
                "page_reference": c.page_reference,
            }
            for c in criteria
        ],
    }


@router.post("/reextract/{doc_id}")
async def reextract(
    doc_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Trigger re-extraction for a document (officer-initiated)."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Log officer action
    action = OfficerAction(
        id=str(uuid.uuid4()),
        officer_id=getattr(request.state, "officer_id", "unknown"),
        officer_email=getattr(request.state, "email", "unknown"),
        action_type="reextract",
        target_id=doc_id,
        comment=f"Re-extraction triggered for document {doc_id}",
    )
    db.add(action)
    db.commit()

    from routers.ingestion import process_document
    background_tasks.add_task(process_document, doc_id)

    return {"doc_id": doc_id, "status": "re-extraction queued"}
