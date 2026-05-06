import React, { useState } from 'react';
import { Verdict } from '../types';
import client from '../api/client';
import { useAuth } from '../context/AuthContext';

interface ReviewCardProps {
  verdict: Verdict;
  onResolved: (verdictId: string, newVerdict: string) => void;
}

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

  if (resolved) {
    return (
      <div className="border border-slate-200 rounded-xl p-5 bg-slate-50 opacity-70 transition-opacity">
        <div className={`inline-block px-3 py-1 rounded-lg text-sm font-semibold ${resolvedVerdict === 'ELIGIBLE' ? 'bg-emerald-100 text-emerald-700' : 'bg-red-100 text-red-700'}`}>
          Verdict updated: {resolvedVerdict.replace('_', ' ')}
        </div>
      </div>
    );
  }

  return (
    <div className="border border-slate-200 rounded-xl p-5 bg-white hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-3">
        <div>
          <h4 className="font-semibold text-slate-800">{verdict.criterion_id}</h4>
          <p className="text-sm text-slate-500 mt-0.5">Bidder: {verdict.bidder_id}</p>
        </div>
        <div className="flex items-center gap-3">
          <span className={`text-sm font-semibold ${confColor}`}>{(verdict.confidence_score * 100).toFixed(0)}%</span>
          <span className="px-2 py-0.5 bg-amber-100 text-amber-700 text-xs font-medium rounded-full">MANUAL REVIEW</span>
        </div>
      </div>

      {verdict.ambiguity_reason && (
        <div className="bg-amber-50 rounded-lg p-3 mb-3 border border-amber-100">
          <p className="text-sm text-amber-800">{verdict.ambiguity_reason}</p>
        </div>
      )}

      <div className="grid grid-cols-2 gap-3 mb-3">
        <div><span className="text-xs text-slate-400">Extracted</span><p className="text-sm font-medium text-slate-700">{verdict.extracted_value || '—'}</p></div>
        <div><span className="text-xs text-slate-400">Threshold</span><p className="text-sm font-medium text-slate-700">{verdict.threshold_value || '—'}</p></div>
      </div>

      {/* Actions for senior_officer */}
      {role === 'senior_officer' && !showActions && (
        <div className="flex gap-2 mt-4">
          <button onClick={() => { setShowActions(true); setSelectedVerdict('ELIGIBLE'); }} className="px-3 py-1.5 text-sm font-medium text-emerald-700 border border-emerald-300 rounded-lg hover:bg-emerald-50 transition-colors">Accept as Eligible</button>
          <button onClick={() => { setShowActions(true); setSelectedVerdict('NOT_ELIGIBLE'); }} className="px-3 py-1.5 text-sm font-medium text-red-700 border border-red-300 rounded-lg hover:bg-red-50 transition-colors">Mark as Not Eligible</button>
        </div>
      )}

      {showActions && (
        <div className="mt-4 p-3 bg-slate-50 rounded-lg border border-slate-200">
          <textarea value={comment} onChange={e => setComment(e.target.value)} placeholder="Enter justification (minimum 20 characters)"
            className="w-full p-2 border border-slate-300 rounded-lg text-sm resize-none h-20 focus:outline-none focus:ring-2 focus:ring-indigo-500" />
          <div className="flex justify-between items-center mt-2">
            <span className={`text-xs ${comment.length >= 20 ? 'text-emerald-600' : 'text-slate-400'}`}>{comment.length}/20 chars</span>
            <div className="flex gap-2">
              <button onClick={() => { setShowActions(false); setSelectedVerdict(null); setComment(''); }} className="px-3 py-1.5 text-sm text-slate-600 hover:bg-slate-100 rounded-lg">Cancel</button>
              <button onClick={handleOverride} disabled={comment.length < 20 || submitting}
                className="px-4 py-1.5 text-sm font-medium text-white bg-indigo-600 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
                {submitting ? 'Submitting...' : 'Submit Override'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReviewCard;
