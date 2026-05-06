"""
Evaluation engine — orchestrates per-criterion verdicts and computes overall bidder verdicts.
All verdicts are INSERT-ONLY (never updated or deleted).
"""
import logging
import uuid
from typing import Dict, List, Optional

from sqlalchemy.orm import Session

from db.models import (
    TenderCriterion, BidderExtractedValue, EvaluationVerdict,
    BidderOverallVerdict, DocumentAuthenticity
)
from services.evaluation.comparators import (
    FinancialComparator, CertificationComparator,
    ExperienceComparator, DocumentationComparator
)
from services.evaluation.arbitration import LLMArbitrator

logger = logging.getLogger(__name__)


class EvaluationEngine:
    """Produces per-criterion and overall verdicts for all bidders in a tender."""

    def __init__(self):
        self.comparators = {
            "financial": FinancialComparator(),
            "technical": ExperienceComparator(),
            "compliance": CertificationComparator(),
            "documentation": DocumentationComparator(),
        }
        self.arbitrator = LLMArbitrator()

    def evaluate_tender(self, tender_id: str, db: Session):
        """
        Run full evaluation for all bidders against all criteria.

        Args:
            tender_id: The tender identifier
            db: Database session
        """
        criteria = db.query(TenderCriterion).filter(
            TenderCriterion.tender_id == tender_id
        ).all()

        all_values = db.query(BidderExtractedValue).filter(
            BidderExtractedValue.tender_id == tender_id
        ).all()

        # Group values by bidder
        bidder_values: Dict[str, List[BidderExtractedValue]] = {}
        for v in all_values:
            if v.bidder_id not in bidder_values:
                bidder_values[v.bidder_id] = []
            bidder_values[v.bidder_id].append(v)

        # Pre-fetch authenticity scores
        auth_scores: Dict[str, float] = {}
        for v in all_values:
            if v.document_id not in auth_scores:
                auth_record = db.query(DocumentAuthenticity).filter(
                    DocumentAuthenticity.document_id == v.document_id
                ).first()
                auth_scores[v.document_id] = auth_record.authenticity_score if auth_record else 100.0

        for bidder_id, values in bidder_values.items():
            value_map = {v.criterion_id: v for v in values}
            verdicts = []
            failing = []
            manual_review = []

            # Find old overall verdict to supersede
            old_overall = db.query(BidderOverallVerdict).filter(
                BidderOverallVerdict.tender_id == tender_id,
                BidderOverallVerdict.bidder_id == bidder_id,
                BidderOverallVerdict.supersedes_id.is_(None)
            ).first()

            overall_uuid = str(uuid.uuid4())
            if old_overall:
                old_overall.supersedes_id = overall_uuid

            # Find old criterion verdicts to supersede
            old_verdicts = db.query(EvaluationVerdict).filter(
                EvaluationVerdict.tender_id == tender_id,
                EvaluationVerdict.bidder_id == bidder_id,
                EvaluationVerdict.supersedes_verdict_id.is_(None)
            ).all()
            old_verdict_map = {v.criterion_id: v for v in old_verdicts}

            for criterion in criteria:
                verdict_uuid = str(uuid.uuid4())
                old_v = old_verdict_map.get(criterion.criterion_id)
                if old_v:
                    old_v.supersedes_verdict_id = verdict_uuid

                extracted = value_map.get(criterion.criterion_id)
                if not extracted:
                    # No value found at all
                    verdict = self._create_verdict(
                        tender_id, bidder_id, criterion,
                        "NOT_ELIGIBLE", 1.0, None,
                        ambiguity_reason=None,
                        reasoning={"reason": "No extracted value found for this criterion"},
                        verdict_uuid=verdict_uuid
                    )
                    verdicts.append(verdict)
                    if criterion.mandatory:
                        failing.append(criterion.criterion_id)
                    continue

                auth_score = auth_scores.get(extracted.document_id, 100.0)
                result = self.evaluate_single(criterion, extracted, auth_score)

                verdict = self._create_verdict(
                    tender_id, bidder_id, criterion,
                    result["verdict"], result["confidence"],
                    extracted,
                    ambiguity_reason=result.get("ambiguity_reason"),
                    reasoning=result.get("reasoning_trace"),
                    llm_model=result.get("llm_model"),
                    verdict_uuid=verdict_uuid
                )
                verdicts.append(verdict)

                if criterion.mandatory:
                    if result["verdict"] == "NOT_ELIGIBLE":
                        failing.append(criterion.criterion_id)
                    elif result["verdict"] == "MANUAL_REVIEW":
                        manual_review.append(criterion.criterion_id)

            # Bulk insert verdicts
            db.bulk_save_objects(verdicts)

            # Compute overall verdict
            if failing:
                overall = "NOT_ELIGIBLE"
            elif manual_review:
                overall = "MANUAL_REVIEW"
            else:
                overall = "ELIGIBLE"

            overall_verdict = BidderOverallVerdict(
                id=overall_uuid,
                tender_id=tender_id,
                bidder_id=bidder_id,
                overall_verdict=overall,
                failing_criteria=failing if failing else None,
                manual_review_criteria=manual_review if manual_review else None,
            )
            db.add(overall_verdict)

        db.commit()
        logger.info(f"Evaluation complete for tender {tender_id}: {len(bidder_values)} bidders")

    def evaluate_single(
        self, criterion: TenderCriterion,
        extracted: BidderExtractedValue,
        authenticity_score: float
    ) -> dict:
        """
        Evaluate a single criterion-value pair.
        Applies ambiguity override first, then type-specific comparator.
        """
        # Ambiguity override checks
        if extracted.confidence_score < 0.65:
            return {
                "verdict": "MANUAL_REVIEW",
                "confidence": extracted.confidence_score,
                "ambiguity_reason": f"Low extraction confidence: {extracted.confidence_score:.2f} < 0.65",
                "reasoning_trace": {"trigger": "low_confidence", "value": extracted.confidence_score},
            }

        if extracted.extraction_status == "contradicted":
            return {
                "verdict": "MANUAL_REVIEW",
                "confidence": extracted.confidence_score,
                "ambiguity_reason": "Contradicted values found across pages",
                "reasoning_trace": {"trigger": "contradicted_value", "extracted": extracted.extracted_value},
            }

        if authenticity_score < 50:
            return {
                "verdict": "MANUAL_REVIEW",
                "confidence": extracted.confidence_score,
                "ambiguity_reason": f"Low document authenticity score: {authenticity_score:.0f} < 50",
                "reasoning_trace": {"trigger": "low_authenticity", "score": authenticity_score},
            }

        # Dispatch to type-specific comparator
        comparator = self.comparators.get(criterion.type, self.comparators["documentation"])
        return comparator.compare(extracted, criterion, self.arbitrator, authenticity_score)

    def _create_verdict(
        self, tender_id, bidder_id, criterion, verdict, confidence,
        extracted, ambiguity_reason=None, reasoning=None, llm_model=None, verdict_uuid=None
    ) -> EvaluationVerdict:
        return EvaluationVerdict(
            verdict_id=verdict_uuid or str(uuid.uuid4()),
            tender_id=tender_id,
            bidder_id=bidder_id,
            criterion_id=criterion.criterion_id,
            verdict=verdict,
            confidence_score=confidence,
            evidence_document_id=extracted.document_id if extracted else None,
            source_page=extracted.source_page if extracted else None,
            extracted_value=extracted.extracted_value if extracted else None,
            threshold_value=criterion.threshold_value,
            ambiguity_reason=ambiguity_reason,
            reasoning_trace=reasoning,
            llm_model_used=llm_model,
        )
