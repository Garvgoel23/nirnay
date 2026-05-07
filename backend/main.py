"""
Nirṇay — FastAPI monolith entry point.
Registers all routers, CORS, auth middleware, startup migration, dashboard summary.
"""
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / ".env", override=True)  # Load backend/.env explicitly

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func

from db.database import engine, get_db, Base
from db.models import Document, EvaluationVerdict, OfficerAction
from routers.auth import AuthMiddleware
from routers import ingestion, extraction, credibility, evaluation, review, notification

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: create tables (dev) or run Alembic migrations (prod)."""
    logger.info("Starting Nirṇay backend...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables ensured")

    # Create storage directories
    os.makedirs(os.getenv("LOCAL_STORAGE_PATH", "./data/uploads"), exist_ok=True)
    os.makedirs(os.getenv("EXPORTS_PATH", "./data/exports"), exist_ok=True)

    yield
    logger.info("Shutting down Nirṇay backend")


app = FastAPI(
    title="Nirṇay API",
    description="Government Procurement Intelligence Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auth middleware
app.add_middleware(AuthMiddleware)

# Register routers
app.include_router(ingestion.router)
app.include_router(extraction.router)
app.include_router(credibility.router)
app.include_router(evaluation.router)
app.include_router(review.router)
app.include_router(notification.router)


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/readyz")
async def readyz():
    return {"status": "ready"}


@app.get("/api/dashboard/summary")
async def dashboard_summary(request: Request, db: Session = Depends(get_db)):
    """Dashboard summary — auth-guarded but not role-restricted."""

    active_tenders = db.query(func.count(func.distinct(Document.tender_id))).filter(
        Document.status != "error"
    ).scalar() or 0

    pending_review_count = db.query(func.count(EvaluationVerdict.verdict_id)).filter(
        EvaluationVerdict.verdict == "MANUAL_REVIEW",
        EvaluationVerdict.supersedes_verdict_id.is_(None),
    ).scalar() or 0

    # ── Rich activity feed: combine uploads + evaluations + officer actions ──
    activity_items = []

    # 1. Recent document uploads (last 15)
    recent_docs = db.query(Document).order_by(Document.created_at.desc()).limit(15).all()
    for doc in recent_docs:
        if not doc.created_at:
            continue
        label = "tender_uploaded" if doc.doc_type == "tender" else "bid_uploaded"
        activity_items.append({
            "id": doc.id,
            "action_type": label,
            "target_id": doc.tender_id,
            "detail": doc.original_filename,
            "actor": doc.department_id or "system",
            "timestamp": str(doc.created_at),
        })

    # 2. Evaluation completions — one entry per tender when first verdict arrived
    from db.models import BidderOverallVerdict
    overall_verdicts = db.query(
        BidderOverallVerdict.tender_id,
        func.min(BidderOverallVerdict.evaluated_at).label("first_verdict_at"),
        func.count(BidderOverallVerdict.bidder_id).label("bidder_count"),
    ).group_by(BidderOverallVerdict.tender_id).all()
    for ov in overall_verdicts:
        if not ov.first_verdict_at:
            continue
        activity_items.append({
            "id": f"eval_{ov.tender_id}",
            "action_type": "evaluation_complete",
            "target_id": ov.tender_id,
            "detail": f"{ov.bidder_count} bidder(s) evaluated",
            "actor": "AI Engine",
            "timestamp": str(ov.first_verdict_at),
        })

    # 3. Officer actions (all officers, not just current)
    # Join with EvaluationVerdict to get tender_id (target_id on OfficerAction is the verdict_id UUID)
    actions = db.query(OfficerAction).order_by(OfficerAction.timestamp.desc()).limit(20).all()
    verdict_tender_map: dict = {}
    if actions:
        verdict_ids = [a.target_id for a in actions if a.target_id]
        verdicts = db.query(EvaluationVerdict.verdict_id, EvaluationVerdict.tender_id, EvaluationVerdict.bidder_id).filter(
            EvaluationVerdict.verdict_id.in_(verdict_ids)
        ).all()
        verdict_tender_map = {v.verdict_id: (v.tender_id, v.bidder_id) for v in verdicts}

    for a in actions:
        tender_id, bidder_id = verdict_tender_map.get(a.target_id, (a.target_id, None))
        detail = a.comment or (f"Bidder: {bidder_id}" if bidder_id else "")
        activity_items.append({
            "id": a.id,
            "action_type": a.action_type,
            "target_id": tender_id,           # human-readable tender ID
            "detail": detail,
            "actor": a.officer_email or a.officer_id or "officer",
            "timestamp": str(a.timestamp) if a.timestamp else None,
        })

    # Sort all by timestamp desc, take top 15
    activity_items.sort(key=lambda x: x["timestamp"] or "", reverse=True)
    recent_activity = activity_items[:15]

    # Completed this month = sign_off actions this calendar month
    from datetime import datetime
    now = datetime.utcnow()
    completed_this_month = sum(
        1 for a in actions
        if a.action_type == "sign_off" and a.timestamp
        and a.timestamp.month == now.month and a.timestamp.year == now.year
    )

    return {
        "active_tenders": active_tenders,
        "pending_review_count": pending_review_count,
        "completed_this_month": completed_this_month,
        "recent_activity": recent_activity,
    }


@app.get("/api/dashboard/tenders")
async def list_tenders(request: Request, db: Session = Depends(get_db)):
    """List all tenders with their status, bidder count, and anomaly count."""
    # Find all unique tender IDs from documents
    tender_ids = db.query(Document.tender_id).filter(Document.doc_type == "tender").distinct().all()
    tenders = []
    
    from db.models import TenderAnomaly
    for (t_id,) in tender_ids:
        # Get tender doc status
        tender_doc = db.query(Document).filter(Document.tender_id == t_id, Document.doc_type == "tender").first()
        status = tender_doc.status if tender_doc else "unknown"
        department = tender_doc.department_id if tender_doc else "unknown"
        
        # Get bidder count
        bidder_count = db.query(func.count(func.distinct(Document.bidder_id))).filter(
            Document.tender_id == t_id, Document.doc_type == "bidder"
        ).scalar() or 0
        
        # Get anomalies
        anomalies = db.query(TenderAnomaly).filter(TenderAnomaly.tender_id == t_id).all()
        anomaly_count = len(anomalies)
        critical_anomalies = sum(1 for a in anomalies if a.severity == "critical")
        
        # Check if evaluation is done (has verdicts)
        has_verdicts = db.query(EvaluationVerdict).filter(EvaluationVerdict.tender_id == t_id).first() is not None
        
        if has_verdicts:
            overall_status = "evaluated"
        elif status == "extracted":
            overall_status = "ready_for_evaluation"
        else:
            overall_status = status
            
        tenders.append({
            "tender_id": t_id,
            "department_id": department,
            "status": overall_status,
            "bidder_count": bidder_count,
            "anomaly_count": anomaly_count,
            "critical_anomalies": critical_anomalies,
            "created_at": str(tender_doc.created_at) if tender_doc and tender_doc.created_at else None
        })
        
    return {"tenders": sorted(tenders, key=lambda x: x["created_at"] or "", reverse=True)}
