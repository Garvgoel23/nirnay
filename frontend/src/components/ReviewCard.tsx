import React, { useState } from 'react';
import { Verdict } from '../types';
import client from '../api/client';
import { useAuth } from '../context/AuthContext';

interface ReviewCardProps {
  verdict: Verdict;
  onResolved: (verdictId: string, newVerdict: string) => void;
}

const typeBadge: Record<string, string> = {
  financial: 'bg-blue-100 text-blue-700',
  technical: 'bg-purple-100 text-purple-700',
  compliance: 'bg-emerald-100 text-emerald-700',
  documentation: 'bg-slate-100 text-slate-600',
};

const ReviewCard: React.FC<ReviewCardProps> = ({ verdict, onResolved }) => {
  const { role } = useAuth();
  const [showActions, setShowActions] = useState(false);
  const [selectedVerdict, setSelectedVerdict] = useState<'ELIGIBLE' | 'NOT_ELIGIBLE' | null>(null);
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [resolved, setResolved] = useState(false);
  const [resolvedVerdict, setResolvedVerdict] = useState('');

  const handleOverride = async () => {
    if (!selectedVerdict || comment.length < 20) return;
    setSubmitting(true);
    try {
      await client.post(`/api/review/override/${verdict.verdict_id}`, { new_verdict: selectedVerdict, comment });
      setResolved(true);
      setResolvedVerdict(selectedVerdict);
      onResolved(verdict.verdict_id, selectedVerdict);
    } catch (e) {
      console.error('Override failed:', e);
    } finally {
      setSubmitting(false);
    }
  };

  const confColor = verdict.confidence_score >= 0.85 ? 'text-emerald-600' : verdict.confidence_score >= 0.65 ? 'text-amber-600' : 'text-red-600';
  const confBg = verdict.confidence_score >= 0.85 ? 'bg-emerald-500' : verdict.confidence_score >= 0.65 ? 'bg-amber-500' : 'bg-red-500';

  if (resolved) {
    return (
      <div className="border border-slate-200 rounded-xl p-5 bg-slate-50 opacity-70 transition-opacity">
        <div className={`inline-block px-3 py-1 rounded-lg text-sm font-semibold ${resolvedVerdict === 'ELIGIBLE' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>
          ✓ Verdict updated: {resolvedVerdict.replace('_', ' ')}
        </div>
      </div>
    );
  }

  return (
    <div className="border border-slate-200 rounded-xl p-5 bg-white hover:shadow-md transition-shadow">
      {/* Header */}
      <div className="flex justify-between items-start mb-3">
        <div className="flex-1 min-w-0 pr-4">
          {/* Type badge + criterion ID */}
          <div className="flex items-center gap-2 mb-1">
            {verdict.criterion_type && (
              <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${typeBadge[verdict.criterion_type] || 'bg-slate-100 text-slate-600'}`}>
                {verdict.criterion_type}
              </span>
            )}
            <span className="font-mono text-xs text-slate-400">{verdict.criterion_id}</span>
          </div>
          {/* Criterion description — the actual human readable title */}
          {verdict.criterion_description ? (
            <p className="text-sm font-semibold text-slate-800 leading-snug">{verdict.criterion_description}</p>
          ) : (
            <p className="text-sm font-semibold text-slate-800">{verdict.criterion_id}</p>
          )}
          <p className="text-xs text-slate-400 mt-1">Bidder: <span className="font-medium text-slate-600">{verdict.bidder_id}</span></p>
        </div>
        {/* Confidence + badge */}
        <div className="flex flex-col items-end gap-1.5 shrink-0">
          <span className="px-2 py-0.5 bg-amber-100 text-amber-700 text-xs font-semibold rounded-full">MANUAL REVIEW</span>
          <div className="flex items-center gap-1.5">
            <div className="w-16 bg-slate-100 rounded-full h-1.5">
              <div className={`${confBg} h-1.5 rounded-full`} style={{ width: `${verdict.confidence_score * 100}%` }} />
            </div>
            <span className={`text-sm font-semibold ${confColor}`}>{(verdict.confidence_score * 100).toFixed(0)}%</span>
          </div>
        </div>
      </div>

      {/* Ambiguity reason — AI message */}
      {verdict.ambiguity_reason && (
        <div className="bg-amber-50 rounded-lg p-3 mb-3 border border-amber-100">
          <p className="text-xs font-semibold text-amber-600 uppercase tracking-wide mb-1">AI Reason for Review</p>
          <p className="text-sm text-amber-800">{verdict.ambiguity_reason}</p>
        </div>
      )}

      {/* AI reasoning if present */}
      {verdict.reasoning_trace?.llm_reasoning && (
        <div className="bg-slate-50 rounded-lg p-3 mb-3 border border-slate-100">
          <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">AI Reasoning</p>
          <p className="text-sm text-slate-600 leading-relaxed">{verdict.reasoning_trace.llm_reasoning}</p>
        </div>
      )}

      {/* Extracted vs threshold */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-slate-50 rounded-lg p-2.5">
          <span className="text-xs text-slate-400 uppercase tracking-wide">Extracted Value</span>
          <p className="text-sm font-semibold text-slate-700 mt-0.5">{verdict.extracted_value || '—'}</p>
        </div>
        <div className="bg-slate-50 rounded-lg p-2.5">
          <span className="text-xs text-slate-400 uppercase tracking-wide">Required Threshold</span>
          <p className="text-sm font-semibold text-slate-700 mt-0.5">{verdict.threshold_value || '—'}</p>
        </div>
      </div>

      {/* Officer action buttons — visible to all logged-in users (override requires justification) */}
      {!showActions && (
        <div className="flex gap-2 mt-2">
          <button
            onClick={() => { setShowActions(true); setSelectedVerdict('ELIGIBLE'); }}
            className="flex-1 px-3 py-2 text-sm font-medium text-emerald-700 border border-emerald-300 rounded-lg hover:bg-emerald-50 transition-colors"
          >
            ✓ Accept as Eligible
          </button>
          <button
            onClick={() => { setShowActions(true); setSelectedVerdict('NOT_ELIGIBLE'); }}
            className="flex-1 px-3 py-2 text-sm font-medium text-red-700 border border-red-300 rounded-lg hover:bg-red-50 transition-colors"
          >
            ✗ Mark as Not Eligible
          </button>
        </div>
      )}

      {showActions && (
        <div className="mt-3 p-3 bg-slate-50 rounded-lg border border-slate-200">
          <div className="flex gap-2 mb-3">
            {(['ELIGIBLE', 'NOT_ELIGIBLE'] as const).map(v => (
              <button key={v} onClick={() => setSelectedVerdict(v)}
                className={`flex-1 py-1.5 text-sm font-medium rounded-lg border transition-colors ${
                  selectedVerdict === v
                    ? v === 'ELIGIBLE' ? 'bg-emerald-600 text-white border-emerald-600' : 'bg-red-600 text-white border-red-600'
                    : 'border-slate-300 text-slate-600 hover:bg-slate-100'
                }`}>
                {v.replace('_', ' ')}
              </button>
            ))}
          </div>
          <textarea
            value={comment}
            onChange={e => setComment(e.target.value)}
            placeholder="Enter officer justification (minimum 20 characters)…"
            className="w-full p-2.5 border border-slate-300 rounded-lg text-sm resize-none h-20 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
          <div className="flex justify-between items-center mt-2">
            <span className={`text-xs ${comment.length >= 20 ? 'text-emerald-600' : 'text-slate-400'}`}>{comment.length}/20 chars min</span>
            <div className="flex gap-2">
              <button onClick={() => { setShowActions(false); setSelectedVerdict(null); setComment(''); }}
                className="px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100 rounded-lg transition-colors">
                Cancel
              </button>
              <button onClick={handleOverride} disabled={comment.length < 20 || submitting}
                className="px-4 py-1.5 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
                {submitting ? 'Submitting…' : 'Submit Override'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReviewCard;
