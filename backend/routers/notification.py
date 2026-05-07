"""Notification router — letter drafting, report and audit PDF generation."""
import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session
from db.database import get_db
from db.models import BidderOverallVerdict
from services.notification.letter_drafter import RejectionLetterDrafter
from services.notification.report_generator import ReportGenerator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/notification", tags=["Notification"])

@router.post("/draft-letter/{bidder_id}")
async def draft_letter(bidder_id: str, tender_id: str, db: Session = Depends(get_db)):
    drafter = RejectionLetterDrafter()
    letter = drafter.draft(bidder_id, tender_id, db)
    return {"bidder_id": bidder_id, "tender_id": tender_id, "letter_text": letter}

@router.post("/draft-all-letters/{tender_id}")
async def draft_all_letters(tender_id: str, db: Session = Depends(get_db)):
    """Auto-draft rejection letters for all NOT_ELIGIBLE bidders in one call."""
    rejected = db.query(BidderOverallVerdict).filter(
        BidderOverallVerdict.tender_id == tender_id,
        BidderOverallVerdict.overall_verdict == "NOT_ELIGIBLE",
        BidderOverallVerdict.supersedes_id.is_(None),
    ).all()

    if not rejected:
        return {"tender_id": tender_id, "letters": []}

    drafter = RejectionLetterDrafter()
    letters = []
    for ov in rejected:
        try:
            letter_text = drafter.draft(ov.bidder_id, tender_id, db)
            letters.append({"bidder_id": ov.bidder_id, "letter_text": letter_text, "failing_criteria": ov.failing_criteria})
        except Exception as e:
            logger.error(f"Failed to draft letter for {ov.bidder_id}: {e}")
            letters.append({"bidder_id": ov.bidder_id, "letter_text": f"Letter generation failed: {str(e)}", "failing_criteria": ov.failing_criteria})

    return {"tender_id": tender_id, "letters": letters}

@router.post("/report/{tender_id}")
async def generate_report(tender_id: str, db: Session = Depends(get_db)):
    gen = ReportGenerator()
    pdf_bytes = gen.generate_evaluation_report(tender_id, db)
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=nirnay_report_{tender_id}.pdf"})

@router.post("/audit/{tender_id}")
async def generate_audit(tender_id: str, db: Session = Depends(get_db)):
    gen = ReportGenerator()
    pdf_bytes = gen.generate_audit_export(tender_id, db)
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename=nirnay_audit_{tender_id}.pdf"})

@router.get("/rejected-bidders/{tender_id}")
async def get_rejected_bidders(tender_id: str, db: Session = Depends(get_db)):
    rejected = db.query(BidderOverallVerdict).filter(BidderOverallVerdict.tender_id == tender_id, BidderOverallVerdict.overall_verdict == "NOT_ELIGIBLE", BidderOverallVerdict.supersedes_id.is_(None)).all()
    return {"tender_id": tender_id, "bidders": [{"bidder_id": r.bidder_id, "failing_criteria": r.failing_criteria} for r in rejected]}

