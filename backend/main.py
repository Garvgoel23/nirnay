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
    officer_id = getattr(request.state, "officer_id", None)

    active_tenders = db.query(func.count(func.distinct(Document.tender_id))).filter(
        Document.status != "error"
    ).scalar() or 0

    pending_review_count = db.query(func.count(EvaluationVerdict.verdict_id)).filter(
        EvaluationVerdict.verdict == "MANUAL_REVIEW",
        EvaluationVerdict.supersedes_verdict_id.is_(None),
    ).scalar() or 0

    recent_activity = []
    if officer_id:
        actions = db.query(OfficerAction).filter(
            OfficerAction.officer_id == officer_id
        ).order_by(OfficerAction.timestamp.desc()).limit(10).all()
        recent_activity = [
            {
                "id": a.id,
                "action_type": a.action_type,
                "target_id": a.target_id,
                "comment": a.comment,
                "timestamp": str(a.timestamp) if a.timestamp else None,
            }
            for a in actions
        ]

    return {
        "active_tenders": active_tenders,
        "pending_review_count": pending_review_count,
        "recent_activity": recent_activity,
    }
