"""
Tender contradiction checker service.
Uses Gemini 2.5 Pro to identify internal contradictions in tender criteria.
Processes in overlapping windows for large criteria sets.
"""
import json
import logging
import os
import uuid
from typing import List

from sqlalchemy.orm import Session

from db.models import TenderCriterion, TenderContradiction as TenderContradictionDB
from services.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

WINDOW_SIZE = 25
OVERLAP = 5


class TenderContradictionChecker:
    """Checks tender criteria for internal contradictions and ambiguities."""

    def __init__(self):
        self.gemini = GeminiClient(model="gemini-2.5-pro", service_name="contradiction_checker")

    def check(self, tender_id: str, db: Session) -> List[dict]:
        """
        Check all criteria for a tender for contradictions.

        For >50 criteria, processes in overlapping windows of 25 with 5-criterion overlap.

        Args:
            tender_id: The tender identifier
            db: Database session

        Returns:
            List of contradiction dictionaries
        """
        # Pull all criteria
        criteria = db.query(TenderCriterion).filter(
            TenderCriterion.tender_id == tender_id
        ).order_by(TenderCriterion.criterion_id).all()

        if not criteria:
            return []

        # Load prompt template
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "prompts", "contradiction_checker_v1.txt"
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        all_contradictions = []

        if len(criteria) > 50:
            # Process in overlapping windows
            windows = self._create_windows(criteria, WINDOW_SIZE, OVERLAP)
            seen_pairs = set()

            for window in windows:
                window_contradictions = self._check_window(window, prompt_template)
                for c in window_contradictions:
                    # Deduplicate by criterion ID pair
                    pair_key = tuple(sorted(c.get("criterion_ids", [])))
                    if pair_key not in seen_pairs:
                        seen_pairs.add(pair_key)
                        all_contradictions.append(c)
        else:
            all_contradictions = self._check_window(criteria, prompt_template)

        # Write to database
        for c in all_contradictions:
            db_record = TenderContradictionDB(
                id=str(uuid.uuid4()),
                tender_id=tender_id,
                criterion_ids=c.get("criterion_ids", []),
                description=c.get("description", ""),
                contradiction_type=c.get("contradiction_type", "undefined_scope"),
                severity=c.get("severity", "warning"),
                suggested_resolution=c.get("suggested_resolution"),
            )
            db.add(db_record)

        db.commit()

        logger.info(f"Found {len(all_contradictions)} contradictions for tender {tender_id}")
        return all_contradictions

    def _check_window(self, criteria_window: List, prompt_template: str) -> List[dict]:
        """Check a window of criteria for contradictions."""
        # Build numbered criteria list
        criteria_text_parts = []
        for i, c in enumerate(criteria_window, start=1):
            criterion_id = c.criterion_id if hasattr(c, 'criterion_id') else c.get('criterion_id', '')
            description = c.description if hasattr(c, 'description') else c.get('description', '')
            threshold = c.threshold_value if hasattr(c, 'threshold_value') else c.get('threshold_value', '')
            unit = c.threshold_unit if hasattr(c, 'threshold_unit') else c.get('threshold_unit', '')

            line = f"{i}. [{criterion_id}] {description}"
            if threshold:
                line += f" (Threshold: {threshold} {unit or ''})"
            criteria_text_parts.append(line)

        criteria_text = "\n".join(criteria_text_parts)
        prompt = prompt_template.replace("{{CRITERIA_LIST}}", criteria_text)

        try:
            response_text = self.gemini.generate(prompt, json_mode=True)
            contradictions = json.loads(response_text)
            if not isinstance(contradictions, list):
                contradictions = [contradictions]
            return contradictions
        except Exception as e:
            logger.error(f"Contradiction check failed: {e}")
            return []

    @staticmethod
    def _create_windows(items: List, window_size: int, overlap: int) -> List[List]:
        """Create overlapping windows from a list of items."""
        windows = []
        step = window_size - overlap
        for i in range(0, len(items), step):
            window = items[i:i + window_size]
            if window:
                windows.append(window)
        return windows
