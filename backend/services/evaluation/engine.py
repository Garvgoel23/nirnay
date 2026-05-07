"""
Evaluation engine — orchestrates per-bidder batch LLM evaluation and computes overall verdicts.
One LLM call per bidder (batch across all criteria). All verdicts are INSERT-ONLY.
"""
import logging
import uuid
from typing import Dict, List

from sqlalchemy.orm import Session

from db.models import (
    TenderCriterion, BidderExtractedValue, EvaluationVerdict,
    BidderOverallVerdict, DocumentAuthenticity, Document
)
from services.evaluation.arbitration import LLMArbitrator

logger = logging.getLogger(__name__)


class EvaluationEngine:
    """Produces per-criterion and overall verdicts for all bidders in a tender."""

    def __init__(self):
        self.arbitrator = LLMArbitrator()

    def evaluate_tender(self, tender_id: str, db: Session):
        """
        Run full evaluation for all bidders against all criteria.
        Makes exactly ONE LLM call per bidder (batch evaluation).

        Args:
            tender_id: The tender identifier
            db: Database session
        """
        criteria: List[TenderCriterion] = db.query(TenderCriterion).filter(
            TenderCriterion.tender_id == tender_id
        ).all()

        if not criteria:
            logger.warning(f"No criteria found for tender {tender_id}, nothing to evaluate")
            return

        # Collect all bidder IDs from Documents table (source of truth)
        bidder_docs = db.query(Document).filter(
            Document.tender_id == tender_id,
            Document.doc_type == "bidder",
        ).all()
        all_bidder_ids = list({d.bidder_id for d in bidder_docs if d.bidder_id})

        if not all_bidder_ids:
            logger.warning(f"No bidder documents found for tender {tender_id}")
            return

        # Load all extracted values
        all_values: List[BidderExtractedValue] = db.query(BidderExtractedValue).filter(
            BidderExtractedValue.tender_id == tender_id
        ).all()

        # Group values by bidder
        bidder_values: Dict[str, List[BidderExtractedValue]] = {}
        for v in all_values:
            bidder_values.setdefault(v.bidder_id, []).append(v)

        # Pre-fetch authenticity scores
        auth_scores: Dict[str, float] = {}
        for v in all_values:
            if v.document_id not in auth_scores:
                auth_record = db.query(DocumentAuthenticity).filter(
                    DocumentAuthenticity.document_id == v.document_id
                ).first()
                auth_scores[v.document_id] = auth_record.authenticity_score if auth_record else 100.0

        for bidder_id in all_bidder_ids:
            values = bidder_values.get(bidder_id, [])
            value_map: Dict[str, BidderExtractedValue] = {v.criterion_id: v for v in values}

            verdicts = []
            failing = []
            manual_review = []

            # Supersede old overall verdict
            old_overall = db.query(BidderOverallVerdict).filter(
                BidderOverallVerdict.tender_id == tender_id,
                BidderOverallVerdict.bidder_id == bidder_id,
                BidderOverallVerdict.supersedes_id.is_(None)
            ).first()

            overall_uuid = str(uuid.uuid4())
            if old_overall:
                old_overall.supersedes_id = overall_uuid

            # Supersede old criterion verdicts
            old_verdicts = db.query(EvaluationVerdict).filter(
                EvaluationVerdict.tender_id == tender_id,
                EvaluationVerdict.bidder_id == bidder_id,
                EvaluationVerdict.supersedes_verdict_id.is_(None)
            ).all()
            old_verdict_map = {v.criterion_id: v for v in old_verdicts}

            # === ONE LLM CALL PER BIDDER ===
            logger.info(f"Running batch LLM evaluation for bidder {bidder_id} on tender {tender_id}")
            batch_results = self.arbitrator.evaluate_all_criteria(criteria, value_map, auth_scores)

            for criterion in criteria:
                verdict_uuid = str(uuid.uuid4())

                # Link old verdict to new one
                old_v = old_verdict_map.get(criterion.criterion_id)
                if old_v:
                    old_v.supersedes_verdict_id = verdict_uuid

                extracted = value_map.get(criterion.criterion_id)
                result = batch_results.get(criterion.criterion_id, {
                    "verdict": "MANUAL_REVIEW",
                    "confidence": 0.5,
                    "score": 50,
                    "message": "No LLM result returned.",
                    "reasoning": "",
                    "ambiguity_reason": "No LLM result returned for this criterion.",
                    "llm_model": None,
                })

                verdict = EvaluationVerdict(
                    verdict_id=verdict_uuid,
                    tender_id=tender_id,
                    bidder_id=bidder_id,
                    criterion_id=criterion.criterion_id,
                    verdict=result["verdict"],
                    confidence_score=result["confidence"],
                    evidence_document_id=extracted.document_id if extracted else None,
                    source_page=extracted.source_page if extracted else None,
                    extracted_value=extracted.extracted_value if extracted else None,
                    threshold_value=criterion.threshold_value,
                    ambiguity_reason=result.get("ambiguity_reason"),
                    reasoning_trace={
                        "llm_reasoning": result.get("reasoning", ""),
                        "message": result.get("message", ""),
                        "score": result.get("score", 50),
                    },
                    llm_model_used=result.get("llm_model"),
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

            logger.info(
                f"Bidder {bidder_id}: overall={overall}, "
                f"failing={len(failing)}, manual_review={len(manual_review)}"
            )

        logger.info(f"Evaluation complete for tender {tender_id}: {len(all_bidder_ids)} bidders processed")
