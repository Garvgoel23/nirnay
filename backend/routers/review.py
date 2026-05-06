"""Review router — queue, override, sign-off."""
import logging, uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import EvaluationVerdict, OfficerAction, BidderOverallVerdict
from models.verdict import OverrideRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/review", tags=["Review"])

@router.get("/queue/{tender_id}")
async def get_review_queue(tender_id: str, db: Session = Depends(get_db)):
    verdicts = db.query(EvaluationVerdict).filter(EvaluationVerdict.tender_id == tender_id, EvaluationVerdict.verdict == "MANUAL_REVIEW", EvaluationVerdict.supersedes_verdict_id.is_(None)).all()
    return {"tender_id": tender_id, "total_count": len(verdicts), "verdicts": [
        {"verdict_id": v.verdict_id, "bidder_id": v.bidder_id, "criterion_id": v.criterion_id, "verdict": v.verdict, "confidence_score": v.confidence_score, "extracted_value": v.extracted_value, "threshold_value": v.threshold_value, "ambiguity_reason": v.ambiguity_reason, "source_page": v.source_page, "evidence_document_id": v.evidence_document_id, "reasoning_trace": v.reasoning_trace} for v in verdicts]}

@router.post("/override/{verdict_id}")
async def override_verdict(verdict_id: str, body: OverrideRequest, request: Request, db: Session = Depends(get_db)):
    original = db.query(EvaluationVerdict).filter(EvaluationVerdict.verdict_id == verdict_id).first()
    if not original: raise HTTPException(status_code=404, detail="Verdict not found")
    new_verdict = EvaluationVerdict(
        verdict_id=str(uuid.uuid4()), tender_id=original.tender_id, bidder_id=original.bidder_id,
        criterion_id=original.criterion_id, verdict=body.new_verdict, confidence_score=1.0,
        evidence_document_id=original.evidence_document_id, source_page=original.source_page,
        extracted_value=original.extracted_value, threshold_value=original.threshold_value,
        ambiguity_reason=None, reasoning_trace={"officer_override": True, "comment": body.comment, "original_verdict_id": verdict_id},
        llm_model_used=None, supersedes_verdict_id=verdict_id)
    db.add(new_verdict)
    action = OfficerAction(id=str(uuid.uuid4()), officer_id=getattr(request.state, "officer_id", "unknown"), officer_email=getattr(request.state, "email", "unknown"), action_type="override_verdict", target_id=verdict_id, comment=body.comment)
    db.add(action)
    db.commit()
    return {"new_verdict_id": new_verdict.verdict_id, "verdict": body.new_verdict}

@router.post("/signoff/{tender_id}")
async def sign_off(tender_id: str, request: Request, db: Session = Depends(get_db)):
    role = getattr(request.state, "role", "officer")
    if role != "senior_officer": raise HTTPException(status_code=403, detail="Only senior_officer can sign off")
    pending = db.query(EvaluationVerdict).filter(EvaluationVerdict.tender_id == tender_id, EvaluationVerdict.verdict == "MANUAL_REVIEW", EvaluationVerdict.supersedes_verdict_id.is_(None)).count()
    if pending > 0: raise HTTPException(status_code=400, detail=f"{pending} pending reviews remain")
    action = OfficerAction(id=str(uuid.uuid4()), officer_id=getattr(request.state, "officer_id", "unknown"), officer_email=getattr(request.state, "email", "unknown"), action_type="sign_off", target_id=tender_id, comment="Tender evaluation signed off")
    db.add(action)
    db.commit()
    return {"tender_id": tender_id, "status": "signed_off"}
