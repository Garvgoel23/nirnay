"""
PDF report generator using reportlab.
Generates evaluation reports and audit exports with SHA-256 integrity hashes.
"""
import hashlib
import json
import logging
import os
import uuid
from datetime import datetime
from io import BytesIO
from typing import List

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from sqlalchemy.orm import Session

from db.models import (
    EvaluationVerdict, BidderOverallVerdict, TenderCriterion,
    TenderAnomaly, OfficerAction, LLMAuditLog
)

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates PDF evaluation reports and audit exports."""

    def generate_evaluation_report(self, tender_id: str, db: Session) -> bytes:
        """
        Generate full evaluation report PDF.

        Includes cover, criteria summary, per-bidder verdicts, anomalies,
        and SHA-256 integrity hash on the final page.
        """
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm)
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle('CustomTitle', parent=styles['Title'], fontSize=20, spaceAfter=20)
        heading_style = ParagraphStyle('CustomHeading', parent=styles['Heading2'], spaceAfter=10)

        elements = []

        # Cover page
        elements.append(Spacer(1, 2*inch))
        elements.append(Paragraph(f"Evaluation Report", title_style))
        elements.append(Paragraph(f"Tender ID: {tender_id}", styles['Heading3']))
        elements.append(Paragraph(f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}", styles['Normal']))

        # Summary stats
        overall_verdicts = db.query(BidderOverallVerdict).filter(
            BidderOverallVerdict.tender_id == tender_id,
            BidderOverallVerdict.supersedes_id.is_(None),
        ).all()

        total_bidders = len(overall_verdicts)
        eligible = sum(1 for v in overall_verdicts if v.overall_verdict == "ELIGIBLE")
        not_eligible = sum(1 for v in overall_verdicts if v.overall_verdict == "NOT_ELIGIBLE")
        manual_review = sum(1 for v in overall_verdicts if v.overall_verdict == "MANUAL_REVIEW")

        anomalies = db.query(TenderAnomaly).filter(TenderAnomaly.tender_id == tender_id).all()

        summary_data = [
            ["Metric", "Value"],
            ["Total Bidders", str(total_bidders)],
            ["Eligible", str(eligible)],
            ["Not Eligible", str(not_eligible)],
            ["Manual Review", str(manual_review)],
            ["Anomaly Flags", str(len(anomalies))],
        ]

        elements.append(Spacer(1, 30))
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4338ca')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f1f5f9')]),
        ]))
        elements.append(summary_table)
        elements.append(PageBreak())

        # Criteria summary
        criteria = db.query(TenderCriterion).filter(
            TenderCriterion.tender_id == tender_id
        ).order_by(TenderCriterion.type).all()

        elements.append(Paragraph("Criteria Summary", heading_style))

        small_wrap = ParagraphStyle('SmallWrap', parent=styles['Normal'], fontSize=7, leading=9)
        criteria_data = [
            [Paragraph("ID", small_wrap), Paragraph("Type", small_wrap),
             Paragraph("Description", small_wrap), Paragraph("Threshold", small_wrap),
             Paragraph("Mandatory", small_wrap)]
        ]
        for c in criteria:
            threshold = f"{c.threshold_value or '-'} {c.threshold_unit or ''}".strip()
            criteria_data.append([
                Paragraph(c.criterion_id, small_wrap),
                Paragraph(c.type, small_wrap),
                Paragraph(c.description or '', small_wrap),          # full description, word-wrapped
                Paragraph(threshold, small_wrap),
                Paragraph("Yes" if c.mandatory else "No", small_wrap),
            ])

        if len(criteria_data) > 1:
            crit_table = Table(criteria_data, colWidths=[1.0*inch, 0.8*inch, 3.2*inch, 1.0*inch, 0.7*inch])
            crit_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4338ca')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f1f5f9')]),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ]))
            elements.append(crit_table)

        elements.append(PageBreak())

        # Build criteria map for lookup in per-bidder section
        criteria_map = {c.criterion_id: c for c in criteria}

        # Per-bidder verdicts
        for ov in overall_verdicts:
            elements.append(Paragraph(f"Bidder: {ov.bidder_id} — {ov.overall_verdict}", heading_style))
            bidder_verdicts = db.query(EvaluationVerdict).filter(
                EvaluationVerdict.tender_id == tender_id,
                EvaluationVerdict.bidder_id == ov.bidder_id,
                EvaluationVerdict.supersedes_verdict_id.is_(None),
            ).all()

            verdict_data = [
                [Paragraph(h, small_wrap) for h in ["Criterion", "Description", "Verdict", "AI Message", "Extracted", "Threshold", "Conf."]]
            ]
            for v in bidder_verdicts:
                crit_obj = criteria_map.get(v.criterion_id)
                crit_desc = crit_obj.description if crit_obj else ""
                ai_msg = ""
                if isinstance(v.reasoning_trace, dict):
                    ai_msg = v.reasoning_trace.get("message", "") or v.reasoning_trace.get("llm_reasoning", "")[:120]
                verdict_data.append([
                    Paragraph(v.criterion_id, small_wrap),
                    Paragraph(crit_desc[:100] if crit_desc else "", small_wrap),
                    Paragraph(v.verdict, small_wrap),
                    Paragraph(str(ai_msg)[:150], small_wrap),
                    Paragraph(str(v.extracted_value or "-")[:30], small_wrap),
                    Paragraph(str(v.threshold_value or "-")[:20], small_wrap),
                    Paragraph(f"{v.confidence_score:.0%}", small_wrap),
                ])

            if len(verdict_data) > 1:
                v_table = Table(verdict_data, colWidths=[0.9*inch, 1.4*inch, 0.8*inch, 1.8*inch, 0.8*inch, 0.8*inch, 0.5*inch])
                v_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e1b4b')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 7),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f1f5f9')]),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('TOPPADDING', (0, 0), (-1, -1), 4),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ]))
                elements.append(v_table)
                elements.append(Spacer(1, 15))

        # Integrity hash
        all_verdicts = db.query(EvaluationVerdict).filter(
            EvaluationVerdict.tender_id == tender_id
        ).all()
        verdict_json = json.dumps(
            [{"verdict_id": v.verdict_id, "verdict": v.verdict, "bidder_id": v.bidder_id,
              "criterion_id": v.criterion_id, "confidence": v.confidence_score}
             for v in all_verdicts],
            sort_keys=True
        )
        integrity_hash = hashlib.sha256(verdict_json.encode()).hexdigest()

        elements.append(PageBreak())
        elements.append(Paragraph("DOCUMENT INTEGRITY HASH", heading_style))
        elements.append(Paragraph(f"SHA-256: {integrity_hash}", styles['Code']))

        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        # Save to storage
        exports_path = os.getenv("EXPORTS_PATH", "./data/exports")
        report_dir = os.path.join(exports_path, tender_id, "reports")
        os.makedirs(report_dir, exist_ok=True)
        report_path = os.path.join(report_dir, "evaluation_report.pdf")
        with open(report_path, "wb") as f:
            f.write(pdf_bytes)

        logger.info(f"Generated evaluation report for {tender_id}: {len(pdf_bytes)} bytes")
        return pdf_bytes

    def generate_audit_export(self, tender_id: str, db: Session) -> bytes:
        """Generate audit export PDF with all records and integrity hash."""
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(Paragraph(f"Audit Export — {tender_id}", styles['Title']))
        elements.append(Paragraph(f"Generated: {datetime.now().strftime('%d %B %Y, %H:%M')}", styles['Normal']))
        elements.append(Spacer(1, 20))

        # Officer actions
        actions = db.query(OfficerAction).filter(
            OfficerAction.target_id.contains(tender_id)
        ).order_by(OfficerAction.timestamp.desc()).all()

        elements.append(Paragraph("Officer Actions", styles['Heading2']))
        if actions:
            action_data = [["Officer", "Action", "Target", "Timestamp"]]
            for a in actions:
                action_data.append([a.officer_email, a.action_type, a.target_id,
                                    str(a.timestamp)[:19] if a.timestamp else ""])

            a_table = Table(action_data, colWidths=[2*inch, 1.2*inch, 1.5*inch, 1.5*inch])
            a_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4338ca')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(a_table)
        else:
            elements.append(Paragraph("No officer actions recorded.", styles['Normal']))

        # Integrity hash
        verdicts = db.query(EvaluationVerdict).filter(
            EvaluationVerdict.tender_id == tender_id
        ).all()
        audit_json = json.dumps({
            "verdicts": [{"id": v.verdict_id, "verdict": v.verdict} for v in verdicts],
            "actions": [{"id": a.id, "action": a.action_type} for a in actions],
        }, sort_keys=True)
        audit_hash = hashlib.sha256(audit_json.encode()).hexdigest()

        elements.append(Spacer(1, 30))
        elements.append(Paragraph("DOCUMENT INTEGRITY HASH", styles['Heading2']))
        elements.append(Paragraph(f"SHA-256: {audit_hash}", styles['Code']))

        doc.build(elements)
        pdf_bytes = buffer.getvalue()
        buffer.close()

        exports_path = os.getenv("EXPORTS_PATH", "./data/exports")
        audit_dir = os.path.join(exports_path, tender_id, "reports")
        os.makedirs(audit_dir, exist_ok=True)
        with open(os.path.join(audit_dir, "audit_export.pdf"), "wb") as f:
            f.write(pdf_bytes)

        return pdf_bytes
