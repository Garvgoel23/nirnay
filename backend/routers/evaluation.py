"""Evaluation router — run, status, results, single verdict."""
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from db.database import get_db
from db.models import EvaluationVerdict, BidderOverallVerdict, TenderCriterion, BidderExtractedValue, Document
from services.evaluation.engine import EvaluationEngine

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/evaluation", tags=["Evaluation"])
_evaluation_jobs = {}

@router.post("/run/{tender_id}")
async def run_evaluation(tender_id: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    job_id = str(uuid.uuid4())
    _evaluation_jobs[tender_id] = {"job_id": job_id, "status": "processing"}
    background_tasks.add_task(_run_eval, tender_id, job_id)
    return {"job_id": job_id, "status": "queued"}

@router.get("/status/{tender_id}")
async def get_status(tender_id: str, db: Session = Depends(get_db)):
    # Count criteria and bidders from their source-of-truth tables
    crit = db.query(func.count(TenderCriterion.criterion_id)).filter(
        TenderCriterion.tender_id == tender_id
    ).scalar() or 0

    # Use Documents table so total is non-zero even before extraction completes
    bidd = db.query(func.count(func.distinct(Document.bidder_id))).filter(
        Document.tender_id == tender_id,
        Document.doc_type == "bidder",
        Document.bidder_id.isnot(None),
    ).scalar() or 0

    total = crit * bidd

    processed = db.query(func.count(EvaluationVerdict.verdict_id)).filter(
        EvaluationVerdict.tender_id == tender_id,
        EvaluationVerdict.supersedes_verdict_id.is_(None)
    ).scalar() or 0

    job_status = _evaluation_jobs.get(tender_id, {}).get("status")

    if job_status in ("complete", "error"):
        status = job_status
    elif total > 0 and processed >= total:
        status = "complete"
    elif job_status == "processing":
        status = "processing"
    else:
        status = "complete" if processed > 0 else "processing"

    return {"tender_id": tender_id, "processed": processed, "total": total, "status": status}

@router.get("/results/{tender_id}")
async def get_results(tender_id: str, db: Session = Depends(get_db)):
    ovs = db.query(BidderOverallVerdict).filter(BidderOverallVerdict.tender_id == tender_id, BidderOverallVerdict.supersedes_id.is_(None)).all()
    bidders = []
    for ov in ovs:
        vs = db.query(EvaluationVerdict).filter(EvaluationVerdict.tender_id == tender_id, EvaluationVerdict.bidder_id == ov.bidder_id, EvaluationVerdict.supersedes_verdict_id.is_(None)).all()
        bidders.append({"bidder_id": ov.bidder_id, "overall_verdict": ov.overall_verdict, "failing_criteria": ov.failing_criteria, "manual_review_criteria": ov.manual_review_criteria,
            "criteria_verdicts": [{"verdict_id": v.verdict_id, "criterion_id": v.criterion_id, "verdict": v.verdict, "confidence_score": v.confidence_score, "extracted_value": v.extracted_value, "threshold_value": v.threshold_value, "ambiguity_reason": v.ambiguity_reason, "source_page": v.source_page, "evidence_document_id": v.evidence_document_id} for v in vs]})
    criteria = db.query(TenderCriterion).filter(TenderCriterion.tender_id == tender_id).all()
    return {"tender_id": tender_id, "bidders": bidders, "total_bidders": len(bidders), "total_criteria": len(criteria), "criteria": [{"criterion_id": c.criterion_id, "description": c.description, "type": c.type} for c in criteria]}

@router.get("/verdict/{verdict_id}")
async def get_verdict(verdict_id: str, db: Session = Depends(get_db)):
    v = db.query(EvaluationVerdict).filter(EvaluationVerdict.verdict_id == verdict_id).first()
    if not v: raise HTTPException(status_code=404, detail="Verdict not found")
    return {"verdict_id": v.verdict_id, "tender_id": v.tender_id, "bidder_id": v.bidder_id, "criterion_id": v.criterion_id, "verdict": v.verdict, "confidence_score": v.confidence_score, "evidence_document_id": v.evidence_document_id, "source_page": v.source_page, "extracted_value": v.extracted_value, "threshold_value": v.threshold_value, "ambiguity_reason": v.ambiguity_reason, "reasoning_trace": v.reasoning_trace, "llm_model_used": v.llm_model_used, "supersedes_verdict_id": v.supersedes_verdict_id, "evaluated_at": str(v.evaluated_at) if v.evaluated_at else None}

def _run_eval(tender_id: str, job_id: str):
    from db.database import SessionLocal
    db = SessionLocal()
    try:
        EvaluationEngine().evaluate_tender(tender_id, db)
        _evaluation_jobs[tender_id] = {"job_id": job_id, "status": "complete"}
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        _evaluation_jobs[tender_id] = {"job_id": job_id, "status": "error"}
    finally:
        db.close()
