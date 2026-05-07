// TypeScript interfaces matching backend models

export interface Criterion {
  criterion_id: string;
  type: 'financial' | 'technical' | 'compliance' | 'documentation';
  description: string;
  threshold_value: string | null;
  threshold_unit: string | null;
  mandatory: boolean;
  raw_text_snippet?: string;
  page_reference?: number;
}

export interface ExtractedValue {
  value_id: string;
  criterion_id: string;
  bidder_id: string;
  extracted_value: string | null;
  value_unit: string | null;
  confidence_score: number;
  source_page: number | null;
  source_snippet: string | null;
  extraction_status: 'found_clear' | 'found_ambiguous' | 'not_found' | 'contradicted';
}

export interface Verdict {
  verdict_id: string;
  tender_id: string;
  bidder_id: string;
  criterion_id: string;
  criterion_description?: string;
  criterion_type?: string;
  verdict: 'ELIGIBLE' | 'NOT_ELIGIBLE' | 'MANUAL_REVIEW';
  confidence_score: number;
  evidence_document_id?: string;
  source_page?: number;
  extracted_value?: string;
  threshold_value?: string;
  ambiguity_reason?: string;
  reasoning_trace?: Record<string, any>;
  llm_model_used?: string;
  supersedes_verdict_id?: string;
  evaluated_at?: string;
}

export interface BidderVerdictGroup {
  bidder_id: string;
  overall_verdict: 'ELIGIBLE' | 'NOT_ELIGIBLE' | 'MANUAL_REVIEW';
  criteria_verdicts: Verdict[];
  failing_criteria?: string[];
  manual_review_criteria?: string[];
}

export interface TenderResults {
  tender_id: string;
  bidders: BidderVerdictGroup[];
  total_bidders: number;
  total_criteria: number;
  criteria: { criterion_id: string; description: string; type: string }[];
}

export interface Anomaly {
  id: string;
  anomaly_type: string;
  bidder_ids: string[];
  evidence: Record<string, any>;
  severity: string;
  detected_at?: string;
}

export interface Contradiction {
  contradiction_id?: string;
  criterion_ids: string[];
  description: string;
  contradiction_type: string;
  severity: string;
  suggested_resolution?: string;
}

export interface DashboardSummary {
  active_tenders: number;
  pending_review_count: number;
  completed_this_month: number;
  recent_activity: {
    id: string;
    action_type: string;
    target_id: string;
    detail?: string;
    actor?: string;
    comment?: string;
    timestamp?: string;
  }[];
}

export interface DocumentStatus {
  doc_id: string;
  tender_id: string;
  bidder_id?: string;
  doc_type: string;
  status: string;
  error_message?: string;
  original_filename: string;
}
