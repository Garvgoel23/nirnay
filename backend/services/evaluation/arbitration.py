"""
Batch LLM evaluation — evaluates ALL criteria for a single bidder in one LLM call.
Returns a dict keyed by criterion_id with verdict, confidence, score, message, reasoning.
"""
import json
import logging
import os
from typing import Dict, List

from services.gemini_client import GeminiClient, GeminiError

logger = logging.getLogger(__name__)


class LLMArbitrator:
    """Evaluates all criteria for a bidder in a single batched LLM call."""

    def __init__(self):
        self.gemini = GeminiClient(model="gemini-2.0-flash", service_name="batch_evaluator")

    def evaluate_all_criteria(
        self,
        criteria: list,
        value_map: Dict[str, object],  # criterion_id → BidderExtractedValue or None
        auth_scores: Dict[str, float],  # document_id → authenticity score
    ) -> Dict[str, dict]:
        """
        Evaluate all criteria for one bidder in a single LLM call.

        Args:
            criteria: List of TenderCriterion ORM objects
            value_map: Dict mapping criterion_id → BidderExtractedValue (or None if missing)
            auth_scores: Dict mapping document_id → authenticity score (0–100)

        Returns:
            Dict mapping criterion_id → result dict with keys:
                verdict, confidence, score, message, reasoning, ambiguity_reason
        """
        # Build criteria JSON for prompt
        criteria_list = []
        for c in criteria:
            criteria_list.append({
                "criterion_id": c.criterion_id,
                "type": c.type,
                "description": c.description,
                "threshold_value": c.threshold_value,
                "threshold_unit": c.threshold_unit,
                "mandatory": c.mandatory,
            })

        # Build extracted values JSON for prompt
        extracted_list = []
        overall_auth = 100.0
        for c in criteria:
            ev = value_map.get(c.criterion_id)
            if ev:
                doc_auth = auth_scores.get(ev.document_id, 100.0)
                overall_auth = min(overall_auth, doc_auth)
                extracted_list.append({
                    "criterion_id": c.criterion_id,
                    "extracted_value": ev.extracted_value,
                    "value_unit": ev.value_unit,
                    "confidence_score": ev.confidence_score,
                    "extraction_status": ev.extraction_status,
                    "source_page": ev.source_page,
                    "source_snippet": ev.source_snippet,
                })
            else:
                extracted_list.append({
                    "criterion_id": c.criterion_id,
                    "extracted_value": None,
                    "value_unit": None,
                    "confidence_score": 0.0,
                    "extraction_status": "not_found",
                    "source_page": None,
                    "source_snippet": None,
                })

        # Load and fill prompt template
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "prompts", "batch_evaluation_v1.txt"
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        prompt = prompt_template.replace("{{CRITERIA_JSON}}", json.dumps(criteria_list, indent=2))
        prompt = prompt.replace("{{EXTRACTED_VALUES_JSON}}", json.dumps(extracted_list, indent=2))
        prompt = prompt.replace("{{AUTHENTICITY_SCORE}}", str(round(overall_auth, 1)))

        logger.info(f"batch_evaluate called for {len(criteria)} criteria, auth_score={overall_auth:.1f}")

        try:
            response_text = self.gemini.generate(prompt, json_mode=True)
            logger.info("Groq response received for batch evaluation")
            raw = json.loads(response_text)

            # Handle both {"results": [...]} and direct list
            if isinstance(raw, dict):
                items = raw.get("results", [])
                if not items:
                    # Try first list value
                    for v in raw.values():
                        if isinstance(v, list):
                            items = v
                            break
            elif isinstance(raw, list):
                items = raw
            else:
                items = []

        except Exception as e:
            logger.error(f"Batch evaluation LLM call failed: {e}")
            # Fallback: mark everything as MANUAL_REVIEW
            return {
                c.criterion_id: {
                    "verdict": "MANUAL_REVIEW",
                    "confidence": 0.5,
                    "score": 50,
                    "message": f"LLM evaluation failed: {str(e)[:120]}",
                    "reasoning": str(e),
                    "ambiguity_reason": f"LLM batch call failed: {str(e)[:120]}",
                    "llm_model": "llama-3.1-8b-instant",
                }
                for c in criteria
            }

        # Build result map
        results: Dict[str, dict] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            cid = item.get("criterion_id")
            if not cid:
                continue
            verdict = item.get("verdict", "MANUAL_REVIEW")
            confidence = float(item.get("confidence", 0.5))
            score = int(item.get("score", 50))
            message = item.get("message", "")
            reasoning = item.get("reasoning", "")

            # Safety: only override ELIGIBLE → MANUAL_REVIEW if confidence is truly very low
            # Threshold is 0.55 to match the decisional prompt — we want the LLM to decide
            if verdict == "ELIGIBLE" and confidence < 0.55:
                verdict = "MANUAL_REVIEW"
                reasoning += " [Overridden: confidence below 0.55 — evidence too weak to confirm ELIGIBLE]"

            ambiguity_reason = None
            if verdict == "MANUAL_REVIEW":
                ambiguity_reason = message[:250] if message else reasoning[:250]

            results[cid] = {
                "verdict": verdict,
                "confidence": confidence,
                "score": score,
                "message": message,
                "reasoning": reasoning,
                "ambiguity_reason": ambiguity_reason,
                "llm_model": "llama-3.1-8b-instant",
            }

        # Ensure every criterion has a result (fill missing with MANUAL_REVIEW)
        for c in criteria:
            if c.criterion_id not in results:
                logger.warning(f"LLM did not return result for criterion {c.criterion_id}, defaulting to MANUAL_REVIEW")
                results[c.criterion_id] = {
                    "verdict": "MANUAL_REVIEW",
                    "confidence": 0.5,
                    "score": 50,
                    "message": "LLM did not return a verdict for this criterion.",
                    "reasoning": "Missing from LLM batch response.",
                    "ambiguity_reason": "LLM did not return a verdict for this criterion.",
                    "llm_model": "llama-3.1-8b-instant",
                }

        return results
