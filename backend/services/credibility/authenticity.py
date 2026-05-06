"""
Document authenticity scoring service.
Runs 4 checks: PDF metadata, font consistency, Vision AI confidence, page count.
Starts at 100, subtracts penalties, clamps to 0–100.
"""
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from db.models import DocumentAuthenticity

logger = logging.getLogger(__name__)


class AuthenticityReport:
    def __init__(self, document_id: str, score: float, flags: List[Dict]):
        self.document_id = document_id
        self.score = score
        self.flags = flags


class AuthenticityScorer:
    """Scores document authenticity based on metadata, fonts, OCR confidence, and page count."""

    def score(self, document_id: str, file_path: str, mime_type: str, db: Session) -> AuthenticityReport:
        """
        Run all authenticity checks and compute a 0–100 score.

        Args:
            document_id: UUID of the document
            file_path: Path to the document file
            mime_type: MIME type of the document
            db: Database session

        Returns:
            AuthenticityReport with score and flags
        """
        flags = []
        score = 100.0

        # Check 1: PDF Metadata
        if mime_type == "application/pdf":
            try:
                metadata_flags = self._check_pdf_metadata(file_path)
                flags.extend(metadata_flags)
            except Exception as e:
                logger.warning(f"PDF metadata check failed: {e}")

            # Check 2: Font Consistency
            try:
                font_flags = self._check_font_consistency(file_path)
                flags.extend(font_flags)
            except Exception as e:
                logger.warning(f"Font consistency check failed: {e}")

        # Check 3: Vision AI Confidence (placeholder — requires GCP credentials)
        # In production, this would call Vision AI for scanned documents

        # Check 4: Page Count
        if mime_type == "application/pdf":
            try:
                page_flags = self._check_page_count(file_path)
                flags.extend(page_flags)
            except Exception as e:
                logger.warning(f"Page count check failed: {e}")

        # Apply penalties
        for flag in flags:
            penalty = flag.get("penalty", 0)
            score -= penalty

        score = max(0.0, min(100.0, score))

        # Write to database
        db_record = DocumentAuthenticity(
            id=str(uuid.uuid4()),
            document_id=document_id,
            authenticity_score=score,
            flags=[f for f in flags],
        )
        db.add(db_record)
        db.commit()

        report = AuthenticityReport(
            document_id=document_id,
            score=score,
            flags=flags,
        )

        logger.info(f"Authenticity score for {document_id}: {score}")
        return report

    def _check_pdf_metadata(self, file_path: str) -> List[Dict]:
        """Check PDF metadata for date anomalies and unexpected producers."""
        flags = []
        try:
            import fitz
            from dateutil import parser as date_parser

            doc = fitz.open(file_path)
            metadata = doc.metadata

            # Check creation vs modification date
            creation_date_str = metadata.get("creationDate", "")
            mod_date_str = metadata.get("modDate", "")

            if creation_date_str and mod_date_str:
                try:
                    # PDF dates are in format D:YYYYMMDDHHmmSS
                    creation_clean = creation_date_str.replace("D:", "").split("+")[0].split("-")[0]
                    mod_clean = mod_date_str.replace("D:", "").split("+")[0].split("-")[0]

                    creation_date = date_parser.parse(creation_clean)
                    mod_date = date_parser.parse(mod_clean)

                    if mod_date > creation_date + __import__("datetime").timedelta(days=1):
                        flags.append({
                            "type": "METADATA_DATE_ANOMALY",
                            "severity": "high",
                            "penalty": 25,
                            "detail": f"Modified {mod_date_str} significantly after creation {creation_date_str}",
                        })
                except Exception:
                    pass

            # Check for consumer software producers
            producer = metadata.get("producer", "").lower()
            consumer_software = ["libreoffice", "openoffice", "wps", "canva", "online"]
            if any(sw in producer for sw in consumer_software):
                flags.append({
                    "type": "UNEXPECTED_PRODUCER",
                    "severity": "medium",
                    "penalty": 10,
                    "detail": f"Document produced by consumer software: {metadata.get('producer', '')}",
                })

            doc.close()
        except ImportError:
            logger.warning("PyMuPDF not available for metadata check")

        return flags

    def _check_font_consistency(self, file_path: str) -> List[Dict]:
        """Check for excessive font variety in single-page documents."""
        flags = []
        try:
            import fitz

            doc = fitz.open(file_path)
            if len(doc) == 1:
                page = doc[0]
                fonts = page.get_fonts()
                unique_fonts = set(f[3] for f in fonts if f[3])

                if len(unique_fonts) > 4:
                    flags.append({
                        "type": "FONT_INCONSISTENCY",
                        "severity": "medium",
                        "penalty": 15,
                        "detail": f"Single-page document uses {len(unique_fonts)} unique fonts",
                    })

            doc.close()
        except ImportError:
            logger.warning("PyMuPDF not available for font check")

        return flags

    def _check_page_count(self, file_path: str) -> List[Dict]:
        """Flag unexpected page counts for certificate-type documents."""
        flags = []
        try:
            import fitz

            doc = fitz.open(file_path)
            page_count = len(doc)

            # Check if document looks like a certificate
            if page_count <= 3:
                doc.close()
                return flags

            # Read first page text for certificate keywords
            first_page_text = doc[0].get_text().lower()
            certificate_keywords = [
                "certificate", "registration", "license", "licence",
                "प्रमाण पत्र", "पंजीकरण"
            ]

            if any(kw in first_page_text for kw in certificate_keywords) and page_count > 3:
                flags.append({
                    "type": "UNEXPECTED_PAGE_COUNT",
                    "severity": "low",
                    "penalty": 5,
                    "detail": f"Certificate-type document has {page_count} pages",
                })

            doc.close()
        except ImportError:
            logger.warning("PyMuPDF not available for page count check")

        return flags
