"""
Tender criteria extraction service.
Uses Gemini to extract eligibility criteria from tender documents.
Applies mandatory keyword detection in English and Hindi.
"""
import json
import logging
import os
import re
import uuid
from typing import List

from sqlalchemy.orm import Session

from models.bidder import PageContent
from models.tender import ExtractedCriterion
from services.gemini_client import GeminiClient
from db.models import TenderCriterion, Document

logger = logging.getLogger(__name__)

# Mandatory keywords (English + Hindi)
MANDATORY_KEYWORDS = [
    "shall", "must", "required", "mandatory", "essential", "compulsory",
    "अनिवार्य", "आवश्यक"
]

DESIRABLE_KEYWORDS = [
    "preferred", "desirable", "may", "should", "where applicable",
    "if available", "वांछनीय"
]


class TenderCriteriaExtractor:
    """Extracts eligibility criteria from tender document pages using Gemini."""

    def __init__(self):
        self.gemini = GeminiClient(model="gemini-2.0-flash", service_name="tender_extractor")

    def extract(
        self,
        tender_id: str,
        department_id: str,
        pages: List[PageContent],
        db: Session,
    ) -> List[ExtractedCriterion]:
        """
        Extract all eligibility criteria from tender document pages.

        Args:
            tender_id: The tender identifier
            department_id: The department identifier
            pages: List of extracted page contents
            db: Database session

        Returns:
            List of ExtractedCriterion objects
        """
        # Limit to first 15 pages to avoid hitting Groq's 12K TPM limit (~10K tokens max)
        pages_to_process = pages[:15]
        
        # Concatenate page texts with markers
        page_texts = []
        for page in pages_to_process:
            page_texts.append(f"--- PAGE {page.page_num} ---\n{page.raw_text}")
        concatenated = "\n\n".join(page_texts)

        # Load prompt
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "prompts", "tender_extractor_v1.txt"
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        # Inject document text into prompt
        prompt = prompt_template.replace("{{DOCUMENT_TEXT}}", concatenated)

        # Call Gemini
        response_text = self.gemini.generate(prompt, json_mode=True)

        # Parse response
        try:
            raw_criteria = json.loads(response_text)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse criteria JSON: {e}")
            raw_criteria = []

        if isinstance(raw_criteria, dict):
            # Groq json_object mode forces a dict response.
            # Find the first list value within the dict.
            for val in raw_criteria.values():
                if isinstance(val, list):
                    raw_criteria = val
                    break
            else:
                raw_criteria = [raw_criteria]

        if not isinstance(raw_criteria, list):
            raw_criteria = [raw_criteria]

        # Process and validate each criterion
        criteria: List[ExtractedCriterion] = []
        for seq, raw in enumerate(raw_criteria, start=1):
            criterion_id = f"{tender_id}_C{seq:03d}"

            # Mandatory keyword detection
            raw_snippet = raw.get("raw_text_snippet", "")
            mandatory = self._detect_mandatory(raw_snippet, raw.get("mandatory", True))

            criterion = ExtractedCriterion(
                criterion_id=criterion_id,
                type=raw.get("type", "documentation"),
                description=raw.get("description", ""),
                threshold_value=raw.get("threshold_value"),
                threshold_unit=raw.get("threshold_unit"),
                mandatory=mandatory,
                raw_text_snippet=raw_snippet,
                page_reference=raw.get("page_reference"),
            )
            criteria.append(criterion)

        # Bulk insert into database
        db_criteria = []
        for c in criteria:
            db_criterion = TenderCriterion(
                criterion_id=c.criterion_id,
                tender_id=tender_id,
                department_id=department_id,
                type=c.type,
                description=c.description,
                threshold_value=c.threshold_value,
                threshold_unit=c.threshold_unit,
                mandatory=c.mandatory,
                raw_text_snippet=c.raw_text_snippet,
                page_reference=c.page_reference,
            )
            db_criteria.append(db_criterion)

        db.bulk_save_objects(db_criteria)
        db.commit()

        logger.info(f"Extracted {len(criteria)} criteria for tender {tender_id}")
        return criteria

    def _detect_mandatory(self, raw_text: str, llm_classification: bool) -> bool:
        """
        Detect mandatory vs desirable using keyword matching.
        Falls back to LLM classification if no keywords found.
        """
        text_lower = raw_text.lower()

        has_mandatory = any(kw in text_lower for kw in MANDATORY_KEYWORDS)
        has_desirable = any(kw in text_lower for kw in DESIRABLE_KEYWORDS)

        if has_mandatory and not has_desirable:
            return True
        elif has_desirable and not has_mandatory:
            return False
        else:
            # Neither or both found — use LLM classification
            return llm_classification
