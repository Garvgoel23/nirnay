"""
Ingestion router — upload endpoints for tender and bidder documents.
Includes background task orchestration for OCR + extraction pipeline.
"""
import logging
import os
import uuid
from typing import List

from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from db.database import get_db
from db.models import Document, DocumentPage, TenderCriterion
from models.bidder import DocumentUploadResponse, DocumentStatusResponse, PageContent
from storage.local_storage import get_storage_backend
from services.ocr.pdf_extractor import extract_pdf
from services.ocr.docai_extractor import extract_with_tesseract
from services.ocr.docx_extractor import extract_docx
from services.extraction.tender_extractor import TenderCriteriaExtractor
from services.extraction.bidder_extractor import BidderValueExtractor
from services.credibility.authenticity import AuthenticityScorer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ingestion", tags=["Ingestion"])

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "image/png", "image/jpeg", "image/tiff",
}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/tender", response_model=DocumentUploadResponse, status_code=202)
async def upload_tender(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    department_id: str = Form(...),
    tender_id: str = Form(...),
    db: Session = Depends(get_db),
):
    """Upload a tender document. Processing starts in the background."""
    return await _handle_upload(
        background_tasks, request, file, department_id, tender_id,
        None, "tender", db
    )


@router.post("/bidder", response_model=DocumentUploadResponse, status_code=202)
async def upload_bidder(
    background_tasks: BackgroundTasks,
    request: Request,
    file: UploadFile = File(...),
    department_id: str = Form(...),
    tender_id: str = Form(...),
    bidder_id: str = Form(...),
    db: Session = Depends(get_db),
):
    """Upload a bidder submission document. Processing starts in the background."""
    return await _handle_upload(
        background_tasks, request, file, department_id, tender_id,
        bidder_id, "bidder", db
    )


@router.get("/status/{doc_id}", response_model=DocumentStatusResponse)
async def get_status(doc_id: str, db: Session = Depends(get_db)):
    """Get processing status of an uploaded document."""
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    return DocumentStatusResponse(
        doc_id=doc.id,
        tender_id=doc.tender_id,
        bidder_id=doc.bidder_id,
        doc_type=doc.doc_type,
        status=doc.status,
        error_message=doc.error_message,
        original_filename=doc.original_filename,
    )


async def _handle_upload(
    background_tasks, request, file, department_id, tender_id,
    bidder_id, doc_type, db
):
    """Common upload handler for tender and bidder documents."""
    # Validate MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {ALLOWED_MIME_TYPES}"
        )

    # Read file
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"File exceeds {MAX_FILE_SIZE // (1024*1024)}MB limit")

    doc_id = str(uuid.uuid4())
    storage = get_storage_backend()
    storage_path = f"{tender_id}/{doc_type}/{doc_id}_{file.filename}"
    storage.save(file_bytes, storage_path)

    # Insert document record
    doc = Document(
        id=doc_id,
        tender_id=tender_id,
        bidder_id=bidder_id,
        department_id=department_id,
        doc_type=doc_type,
        original_filename=file.filename,
        storage_path=storage_path,
        mime_type=file.content_type,
        file_size_bytes=len(file_bytes),
        status="uploaded",
    )
    db.add(doc)
    db.commit()

    # Enqueue background processing
    background_tasks.add_task(process_document, doc_id)

    return DocumentUploadResponse(doc_id=doc_id, status="accepted")


def process_document(doc_id: str):
    """Background task: OCR → extraction → authenticity scoring."""
    from db.database import SessionLocal
    db = SessionLocal()

    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            logger.error(f"Document {doc_id} not found")
            return

        storage = get_storage_backend()
        storage_path = os.path.join(storage.base_path, doc.storage_path)

        # OCR phase
        doc.status = "ocr_processing"
        db.commit()

        pages: List[PageContent] = []
        try:
            if doc.mime_type == "application/pdf":
                pages = extract_pdf(storage_path)
                # Fallback pages with insufficient text to Tesseract
                for i, page in enumerate(pages):
                    if page.needs_documentai:
                        fallback_pages = extract_with_tesseract(storage_path, doc.mime_type)
                        for fp in fallback_pages:
                            if fp.page_num == page.page_num:
                                pages[i] = fp
                                break

            elif doc.mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                pages = extract_docx(storage_path)

            elif doc.mime_type.startswith("image/"):
                pages = extract_with_tesseract(storage_path, doc.mime_type)

        except Exception as e:
            doc.status = "error"
            doc.error_message = f"OCR failed: {str(e)}"
            db.commit()
            return

        # Save pages to database
        for page in pages:
            db_page = DocumentPage(
                id=str(uuid.uuid4()),
                document_id=doc_id,
                page_num=page.page_num,
                raw_text=page.raw_text,
                extraction_method=page.extraction_method,
                confidence_avg=page.confidence_avg,
                word_count=page.word_count,
            )
            db.add(db_page)

        doc.status = "ocr_complete"
        db.commit()

        # Extraction phase
        doc.status = "extracting"
        db.commit()

        try:
            if doc.doc_type == "tender":
                extractor = TenderCriteriaExtractor()
                extractor.extract(doc.tender_id, doc.department_id, pages, db)

            elif doc.doc_type == "bidder":
                import time
                max_retries = 30
                for _ in range(max_retries):
                    tender_doc = db.query(Document).filter(
                        Document.tender_id == doc.tender_id,
                        Document.doc_type == "tender"
                    ).first()
                    if tender_doc and tender_doc.status in ("extracted", "error"):
                        break
                    # Session rollback to ensure fresh read on next iteration
                    db.rollback()
                    time.sleep(2)

                # Pull existing criteria for this tender
                criteria = db.query(TenderCriterion).filter(
                    TenderCriterion.tender_id == doc.tender_id
                ).all()

                if criteria:
                    from models.tender import ExtractedCriterion
                    criteria_models = [
                        ExtractedCriterion(
                            criterion_id=c.criterion_id,
                            type=c.type,
                            description=c.description,
                            threshold_value=c.threshold_value,
                            threshold_unit=c.threshold_unit,
                            mandatory=c.mandatory,
                        )
                        for c in criteria
                    ]
                    extractor = BidderValueExtractor()
                    extractor.extract(
                        doc.bidder_id, doc.tender_id, doc.id,
                        pages, criteria_models, db
                    )

            # Run authenticity scoring
            scorer = AuthenticityScorer()
            scorer.score(doc.id, storage_path, doc.mime_type, db)

            doc.status = "extracted"
            db.commit()

        except Exception as e:
            doc.status = "error"
            doc.error_message = f"Extraction failed: {str(e)}"
            db.commit()
            logger.error(f"Extraction failed for {doc_id}: {e}")

    except Exception as e:
        logger.error(f"Process document failed for {doc_id}: {e}")
    finally:
        db.close()
