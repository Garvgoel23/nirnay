"""
Type-specific comparators for bid evaluation.
Financial, Certification, Experience, and Documentation comparators.
"""
import logging
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional

logger = logging.getLogger(__name__)

# Unit normalisation multipliers (to rupees)
UNIT_MULTIPLIERS = {
    "crores": 10000000,
    "crore": 10000000,
    "lakhs": 100000,
    "lakh": 100000,
    "thousands": 1000,
    "thousand": 1000,
    "rupees": 1,
    "rs": 1,
}


class FinancialComparator:
    """Compares financial values against thresholds with unit normalisation."""

    def compare(self, extracted, criterion, arbitrator, authenticity_score) -> dict:
        try:
            ext_val = self._parse_value(extracted.extracted_value, extracted.value_unit)
            thr_val = self._parse_value(criterion.threshold_value, criterion.threshold_unit)
        except (InvalidOperation, ValueError, TypeError):
            return {
                "verdict": "MANUAL_REVIEW",
                "confidence": extracted.confidence_score,
                "ambiguity_reason": "Could not parse financial values for comparison",
                "reasoning_trace": {
                    "extracted_raw": extracted.extracted_value,
                    "threshold_raw": criterion.threshold_value,
                },
            }

        if thr_val == 0:
            return {"verdict": "ELIGIBLE", "confidence": 0.95, "reasoning_trace": {"note": "Zero threshold"}}

        # Check if within 5% borderline
        ratio = abs(ext_val - thr_val) / thr_val
        if ratio <= 0.05:
            # Route to LLM arbitration
            result = arbitrator.arbitrate(criterion, extracted, authenticity_score)
            return result

        if ext_val >= thr_val:
            return {
                "verdict": "ELIGIBLE",
                "confidence": min(extracted.confidence_score, 0.95),
                "reasoning_trace": {
                    "extracted_normalised": float(ext_val),
                    "threshold_normalised": float(thr_val),
                    "unit": "rupees",
                },
            }
        else:
            shortfall = float(thr_val - ext_val)
            return {
                "verdict": "NOT_ELIGIBLE",
                "confidence": min(extracted.confidence_score, 0.95),
                "reasoning_trace": {
                    "extracted_normalised": float(ext_val),
                    "threshold_normalised": float(thr_val),
                    "shortfall": shortfall,
                    "unit": "rupees",
                },
            }

    @staticmethod
    def _parse_value(value_str: str, unit: str) -> Decimal:
        if not value_str:
            return Decimal(0)
        clean = re.sub(r"[,\s₹]", "", str(value_str))
        clean = re.sub(r"^[Rr][Ss]\.?\s*", "", clean)
        amount = Decimal(clean)
        multiplier = UNIT_MULTIPLIERS.get((unit or "").lower(), 1)
        return amount * multiplier


class CertificationComparator:
    """Checks certification presence and expiry."""

    def compare(self, extracted, criterion, arbitrator, authenticity_score) -> dict:
        if extracted.extraction_status == "found_clear":
            # Check expiry if present
            expiry = self._extract_expiry(extracted.extracted_value)
            if expiry and expiry < datetime.now():
                return {
                    "verdict": "NOT_ELIGIBLE",
                    "confidence": 0.90,
                    "reasoning_trace": {"reason": "CERTIFICATE_EXPIRED", "expiry_date": str(expiry)},
                }
            return {
                "verdict": "ELIGIBLE",
                "confidence": min(extracted.confidence_score, 0.95),
                "reasoning_trace": {"status": "certificate_found_valid"},
            }

        if extracted.extraction_status == "not_found":
            return {
                "verdict": "NOT_ELIGIBLE",
                "confidence": 0.90,
                "reasoning_trace": {"reason": "certificate_not_found"},
            }

        # found_ambiguous or other
        return {
            "verdict": "MANUAL_REVIEW",
            "confidence": extracted.confidence_score,
            "ambiguity_reason": f"Certificate status: {extracted.extraction_status}",
            "reasoning_trace": {"status": extracted.extraction_status},
        }

    @staticmethod
    def _extract_expiry(value: str) -> Optional[datetime]:
        if not value:
            return None
        date_patterns = [
            r"(\d{2}[/-]\d{2}[/-]\d{4})",
            r"(\d{4}[/-]\d{2}[/-]\d{2})",
            r"(\d{2}\s+\w+\s+\d{4})",
        ]
        for pattern in date_patterns:
            match = re.search(pattern, value)
            if match:
                try:
                    from dateutil import parser
                    return parser.parse(match.group(1), dayfirst=True)
                except Exception:
                    continue
        return None


class ExperienceComparator:
    """Compares project count against required minimum."""

    def compare(self, extracted, criterion, arbitrator, authenticity_score) -> dict:
        try:
            found_count = int(re.search(r"\d+", str(extracted.extracted_value or "0")).group())
            required_count = int(re.search(r"\d+", str(criterion.threshold_value or "0")).group())
        except (AttributeError, ValueError):
            return {
                "verdict": "MANUAL_REVIEW",
                "confidence": extracted.confidence_score,
                "ambiguity_reason": "Could not parse experience count values",
                "reasoning_trace": {
                    "extracted_raw": extracted.extracted_value,
                    "threshold_raw": criterion.threshold_value,
                },
            }

        if found_count >= required_count:
            return {
                "verdict": "ELIGIBLE",
                "confidence": min(extracted.confidence_score, 0.95),
                "reasoning_trace": {"found_count": found_count, "required_count": required_count},
            }
        else:
            return {
                "verdict": "NOT_ELIGIBLE",
                "confidence": min(extracted.confidence_score, 0.95),
                "reasoning_trace": {"found_count": found_count, "required_count": required_count},
            }


class DocumentationComparator:
    """Checks documentation presence."""

    def compare(self, extracted, criterion, arbitrator, authenticity_score) -> dict:
        if extracted.extraction_status == "found_clear":
            return {
                "verdict": "ELIGIBLE",
                "confidence": min(extracted.confidence_score, 0.95),
                "reasoning_trace": {"status": "document_found"},
            }

        if extracted.extraction_status == "not_found":
            return {
                "verdict": "NOT_ELIGIBLE",
                "confidence": 0.90,
                "reasoning_trace": {"status": "document_not_found"},
            }

        return {
            "verdict": "MANUAL_REVIEW",
            "confidence": extracted.confidence_score,
            "ambiguity_reason": f"Documentation status: {extracted.extraction_status}",
            "reasoning_trace": {"status": extracted.extraction_status},
        }
