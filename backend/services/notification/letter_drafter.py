"""
Rejection letter drafter using Gemini.
Generates formal GoI-format rejection letters.
"""
import logging
import os
from datetime import datetime

from sqlalchemy.orm import Session

from db.models import EvaluationVerdict, TenderCriterion, BidderExtractedValue
from services.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class RejectionLetterDrafter:
    """Drafts formal rejection letters in GoI format."""

    def __init__(self):
        self.gemini = GeminiClient(model="gemini-2.0-flash", service_name="letter_drafter")

    def draft(self, bidder_id: str, tender_id: str, db: Session) -> str:
        """
        Generate a rejection letter for a bidder.

        Args:
            bidder_id: The bidder identifier
            tender_id: The tender identifier
            db: Database session

        Returns:
            Plain text rejection letter
        """
        # Pull NOT_ELIGIBLE verdicts
        verdicts = db.query(EvaluationVerdict).filter(
            EvaluationVerdict.tender_id == tender_id,
            EvaluationVerdict.bidder_id == bidder_id,
            EvaluationVerdict.verdict == "NOT_ELIGIBLE",
            EvaluationVerdict.supersedes_verdict_id.is_(None),
        ).all()

        if not verdicts:
            return "No failing criteria found for this bidder."

        # Build failed criteria list
        failed_criteria = []
        for v in verdicts:
            criterion = db.query(TenderCriterion).filter(
                TenderCriterion.criterion_id == v.criterion_id
            ).first()

            if criterion:
                failed_criteria.append({
                    "criterion_description": criterion.description,
                    "required_value": f"{criterion.threshold_value or 'N/A'} {criterion.threshold_unit or ''}".strip(),
                    "found_value": v.extracted_value or "not found in submitted documents",
                })

        # Load prompt
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "prompts", "rejection_letter_v1.txt"
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        # Get department from first criterion
        department_name = "Government Department"
        first_criterion = db.query(TenderCriterion).filter(
            TenderCriterion.tender_id == tender_id
        ).first()
        if first_criterion:
            department_name = first_criterion.department_id

        import json
        prompt = prompt_template.replace("{{TENDER_ID}}", tender_id)
        prompt = prompt.replace("{{DEPARTMENT_NAME}}", department_name)
        prompt = prompt.replace("{{BIDDER_COMPANY_NAME}}", bidder_id)
        prompt = prompt.replace("{{EVALUATION_DATE}}", datetime.now().strftime("%d-%m-%Y"))
        prompt = prompt.replace("{{YEAR}}", str(datetime.now().year))
        prompt = prompt.replace("{{FAILED_CRITERIA_LIST}}", json.dumps(failed_criteria, indent=2))

        letter_text = self.gemini.generate(prompt, json_mode=False)

        # Save to storage
        exports_path = os.getenv("EXPORTS_PATH", "./data/exports")
        letter_dir = os.path.join(exports_path, tender_id, "letters")
        os.makedirs(letter_dir, exist_ok=True)

        letter_path = os.path.join(letter_dir, f"{bidder_id}_draft.txt")
        with open(letter_path, "w", encoding="utf-8") as f:
            f.write(letter_text)

        logger.info(f"Drafted rejection letter for {bidder_id} saved to {letter_path}")
        return letter_text
