"""
Credibility router — contradiction check, anomaly detection, authenticity endpoints.
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import DocumentAuthenticity, TenderAnomaly, TenderContradiction
from services.credibility.contradiction import TenderContradictionChecker
from services.credibility.anomaly import CrossBidderAnomalyDetector

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/credibility", tags=["Credibility"])


@router.post("/contradictions/{tender_id}")
async def check_contradictions(tender_id: str, db: Session = Depends(get_db)):
    """Run contradiction check on tender criteria."""
    checker = TenderContradictionChecker()
    contradictions = checker.check(tender_id, db)
    return {
        "tender_id": tender_id,
        "total_count": len(contradictions),
        "contradictions": contradictions,
    }


@router.post("/anomalies/{tender_id}")
async def detect_anomalies(tender_id: str, db: Session = Depends(get_db)):
    """Run cross-bidder anomaly detection."""
    detector = CrossBidderAnomalyDetector()
    anomalies = detector.detect(tender_id, db)
    return {
        "tender_id": tender_id,
        "total_count": len(anomalies),
        "anomalies": anomalies,
    }


@router.get("/anomalies/{tender_id}")
async def get_anomalies(tender_id: str, db: Session = Depends(get_db)):
    """Get previously detected anomalies for a tender."""
    anomalies = db.query(TenderAnomaly).filter(
        TenderAnomaly.tender_id == tender_id
    ).all()
    return {
        "tender_id": tender_id,
        "total_count": len(anomalies),
        "anomalies": [
            {
                "id": a.id,
                "anomaly_type": a.anomaly_type,
                "bidder_ids": a.bidder_ids,
                "evidence": a.evidence,
                "severity": a.severity,
                "detected_at": str(a.detected_at) if a.detected_at else None,
            }
            for a in anomalies
        ],
    }


@router.get("/authenticity/{document_id}")
async def get_authenticity(document_id: str, db: Session = Depends(get_db)):
    """Get authenticity report for a document."""
    auth = db.query(DocumentAuthenticity).filter(
        DocumentAuthenticity.document_id == document_id
    ).first()

    if not auth:
        raise HTTPException(status_code=404, detail="Authenticity report not found")

    return {
        "document_id": document_id,
        "authenticity_score": auth.authenticity_score,
        "flags": auth.flags,
        "scored_at": str(auth.scored_at) if auth.scored_at else None,
    }
