"""
LLM arbitration for borderline eligibility verdicts.
Uses Gemini 2.5 Pro with step-by-step reasoning.
"""
import json
import logging
import os

from services.gemini_client import GeminiClient

logger = logging.getLogger(__name__)


class LLMArbitrator:
    """Resolves borderline verdicts via LLM reasoning."""

    def __init__(self):
        self.gemini = GeminiClient(model="gemini-2.5-pro", service_name="arbitration")

    def arbitrate(self, criterion, extracted_value, authenticity_score: float) -> dict:
        """
        Run LLM arbitration for a borderline criterion-value pair.

        Args:
            criterion: The tender criterion
            extracted_value: The extracted bidder value
            authenticity_score: Document authenticity score (0–100)

        Returns:
            Dict with verdict, confidence, reasoning_trace, llm_model
        """
        prompt_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "prompts", "llm_arbitration_v1.txt"
        )
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template = f.read()

        prompt = prompt_template.replace("{{CRITERION_DESCRIPTION}}", criterion.description or "")
        prompt = prompt.replace("{{THRESHOLD_VALUE}}", str(criterion.threshold_value or ""))
        prompt = prompt.replace("{{THRESHOLD_UNIT}}", str(criterion.threshold_unit or ""))
        prompt = prompt.replace("{{EXTRACTED_VALUE}}", str(extracted_value.extracted_value or ""))
        prompt = prompt.replace("{{VALUE_UNIT}}", str(extracted_value.value_unit or ""))
        prompt = prompt.replace("{{CONFIDENCE_SCORE}}", str(extracted_value.confidence_score))
        prompt = prompt.replace("{{OCR_CONFIDENCE}}", str(getattr(extracted_value, 'ocr_confidence', 'N/A')))
        prompt = prompt.replace("{{AUTHENTICITY_SCORE}}", str(authenticity_score))

        try:
            response_text = self.gemini.generate(prompt, json_mode=True)
            result = json.loads(response_text)
        except Exception as e:
            logger.error(f"Arbitration failed: {e}")
            return {
                "verdict": "MANUAL_REVIEW",
                "confidence": 0.5,
                "ambiguity_reason": f"LLM arbitration failed: {str(e)}",
                "reasoning_trace": {"error": str(e)},
                "llm_model": "gemini-2.5-pro",
            }

        verdict = result.get("verdict", "MANUAL_REVIEW")
        confidence = float(result.get("confidence", 0.5))
        reasoning = result.get("reasoning", "")

        # Enforce: ELIGIBLE with low confidence → MANUAL_REVIEW
        if verdict == "ELIGIBLE" and confidence < 0.75:
            verdict = "MANUAL_REVIEW"
            reasoning += " [Overridden: confidence below 0.75 threshold for ELIGIBLE]"

        ambiguity_reason = None
        if verdict == "MANUAL_REVIEW":
            ambiguity_reason = f"LLM arbitration: {reasoning[:200]}"

        return {
            "verdict": verdict,
            "confidence": confidence,
            "ambiguity_reason": ambiguity_reason,
            "reasoning_trace": {"llm_reasoning": reasoning, "raw_result": result},
            "llm_model": "gemini-2.5-pro",
        }
