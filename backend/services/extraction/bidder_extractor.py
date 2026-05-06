"""
Bidder value extraction service.
For each criterion, extracts the corresponding value from bidder documents via Gemini.
"""
import json
import logging
import os
import uuid
from typing import List

from sqlalchemy.orm import Session

from models.bidder import PageContent, ExtractedValue
from models.tender import ExtractedCriterion
from services.gemini_client import GeminiClient
from db.models import BidderExtractedValue, Document

logger = logging.getLogger(__name__)


class BidderValueExtractor:
    """Extracts specific values from bidder documents for each tender criterion."""

    def __init__(self):
        self.gemini = GeminiClient(model="gemini-2.0-flash", service_name="bidder_extractor")

    def extract(
        self,
        bidder_id: str,
        tender_id: str,
        document_id: str,
        pages: List[PageContent],
        criteria: List[ExtractedCriterion],
        db: Session,
    ) -> List[ExtractedValue]:
        """
        Extract values for all criteria from bidder document pages.

        Args:
            bidder_id: The bidder identifier
            tender_id: The tender identifier
            document_id: The document UUID
            pages: List of extracted page contents
            criteria: List of tender criteria to check against
            db: Database session

        Returns:
            List of ExtractedValue objects
        """
        # Limit to first 15 pages to avoid hitting Groq's 12K TPM limit
        pages_to_process = pages[:15]
        
        # Concatenate page texts with markers
        page_texts = []
        for page in pages_to_process:
            page_texts.append(f"--- PAGE {page.page_num} ---\n{page.raw_text}")
        concatenated = "\n\n".join(page_texts)

        # Load prompt template
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "prompts", "bidder_value_extractor_v1.txt"
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        extracted_values: List[ExtractedValue] = []

        for criterion in criteria:
            # Build targeted prompt for this criterion
            prompt = prompt_template.replace("{{CRITERION_DESCRIPTION}}", criterion.description)
            prompt = prompt.replace("{{THRESHOLD_VALUE}}", criterion.threshold_value or "N/A")
            prompt = prompt.replace("{{THRESHOLD_UNIT}}", criterion.threshold_unit or "N/A")
            prompt = prompt.replace("{{CRITERION_TYPE}}", criterion.type)
            prompt = prompt.replace("{{DOCUMENT_TEXT}}", concatenated)

            try:
                response_text = self.gemini.generate(prompt, json_mode=True)
                raw = json.loads(response_text)
            except Exception as e:
                logger.warning(f"Failed to extract value for {criterion.criterion_id}: {e}")
                raw = {
                    "extracted_value": None,
                    "confidence_score": 0.0,
                    "extraction_status": "not_found",
                }

            value = ExtractedValue(
                value_id=str(uuid.uuid4()),
                criterion_id=criterion.criterion_id,
                bidder_id=bidder_id,
                tender_id=tender_id,
                document_id=document_id,
                extracted_value=raw.get("extracted_value"),
                value_unit=raw.get("value_unit"),
                confidence_score=min(max(float(raw.get("confidence_score", 0.0)), 0.0), 1.0),
                source_page=raw.get("source_page"),
                source_snippet=raw.get("source_snippet"),
                extraction_status=raw.get("extraction_status", "not_found"),
            )
            extracted_values.append(value)

        # Bulk insert into database
        db_values = []
        for v in extracted_values:
            db_value = BidderExtractedValue(
                value_id=v.value_id,
                criterion_id=v.criterion_id,
                bidder_id=v.bidder_id,
                tender_id=v.tender_id,
                document_id=v.document_id,
                extracted_value=v.extracted_value,
                value_unit=v.value_unit,
                confidence_score=v.confidence_score,
                source_page=v.source_page,
                source_snippet=v.source_snippet,
                extraction_status=v.extraction_status,
            )
            db_values.append(db_value)

        db.bulk_save_objects(db_values)
        db.commit()

        logger.info(
            f"Extracted {len(extracted_values)} values for bidder {bidder_id} "
            f"on tender {tender_id}"
        )
        return extracted_values
