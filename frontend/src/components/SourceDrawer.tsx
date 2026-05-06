import React, { useEffect, useState } from 'react';
import { Verdict } from '../types';
import client from '../api/client';

interface SourceDrawerProps {
  verdict: Verdict | null;
  onClose: () => void;
}

const SourceDrawer: React.FC<SourceDrawerProps> = ({ verdict, onClose }) => {
  const [detail, setDetail] = useState<any>(null);

  useEffect(() => {
    if (verdict) {
      client.get(`/api/evaluation/verdict/${verdict.verdict_id}`).then(r => setDetail(r.data)).catch(() => {});
    }
  }, [verdict]);

  if (!verdict) return null;
  const d = detail || verdict;

  const confColor = d.confidence_score >= 0.85 ? 'bg-emerald-500' : d.confidence_score >= 0.65 ? 'bg-amber-500' : 'bg-red-500';

  return (
    <>
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/20 z-40" onClick={onClose} />
      {/* Drawer */}
      <div className="fixed right-0 top-0 h-full w-96 bg-white shadow-2xl z-50 animate-slide-in-right overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex justify-between items-start mb-6">
            <div>
              <h3 className="text-lg font-semibold text-slate-800">{d.criterion_id}</h3>
              <p className="text-sm text-slate-500 mt-1">Bidder: {d.bidder_id}</p>
            </div>
            <button onClick={onClose} className="p-1 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600 transition-colors">
              <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor"><path d="M6.28 5.22a.75.75 0 00-1.06 1.06L8.94 10l-3.72 3.72a.75.75 0 101.06 1.06L10 11.06l3.72 3.72a.75.75 0 101.06-1.06L11.06 10l3.72-3.72a.75.75 0 00-1.06-1.06L10 8.94 6.28 5.22z"/></svg>
            </button>
          </div>

          {/* Verdict badge */}
          <div className={`inline-block px-3 py-1.5 rounded-lg text-sm font-semibold mb-4 ${d.verdict === 'ELIGIBLE' ? 'bg-emerald-100 text-emerald-700' : d.verdict === 'NOT_ELIGIBLE' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}`}>
            {d.verdict?.replace('_', ' ')}
          </div>

          {/* Values */}
          <div className="space-y-4">
            <div>
              <label className="text-xs font-medium text-slate-400 uppercase tracking-wider">Extracted Value</label>
              <p className="text-sm text-slate-700 mt-1">{d.extracted_value || '—'}</p>
            </div>
            <div>
              <label className="text-xs font-medium text-slate-400 uppercase tracking-wider">Threshold Value</label>
              <p className="text-sm text-slate-700 mt-1">{d.threshold_value || '—'}</p>
            </div>

            {/* Confidence bar */}
            <div>
              <label className="text-xs font-medium text-slate-400 uppercase tracking-wider">Confidence Score</label>
              <div className="mt-2 flex items-center gap-2">
                <div className="flex-1 bg-slate-100 rounded-full h-2">
                  <div className={`${confColor} h-2 rounded-full transition-all`} style={{ width: `${(d.confidence_score || 0) * 100}%` }}/>
                </div>
                <span className="text-sm font-medium text-slate-600">{((d.confidence_score || 0) * 100).toFixed(0)}%</span>
              </div>
            </div>

            <div>
              <label className="text-xs font-medium text-slate-400 uppercase tracking-wider">Source Page</label>
              <p className="text-sm text-slate-700 mt-1">{d.source_page || '—'}</p>
            </div>

            {/* Source snippet */}
            {d.reasoning_trace?.source_snippet && (
              <div>
                <label className="text-xs font-medium text-slate-400 uppercase tracking-wider">Source Snippet</label>
                <pre className="mt-2 text-xs font-mono bg-slate-50 p-3 rounded-lg border border-slate-200 whitespace-pre-wrap max-h-40 overflow-y-auto text-slate-600">{d.reasoning_trace.source_snippet}</pre>
              </div>
            )}

            {/* Reasoning trace */}
            {d.reasoning_trace && (
              <div>
                <label className="text-xs font-medium text-slate-400 uppercase tracking-wider">Reasoning</label>
                <div className="mt-2 text-sm text-slate-600 bg-slate-50 p-3 rounded-lg border border-slate-200 max-h-48 overflow-y-auto">
                  {typeof d.reasoning_trace === 'string' ? d.reasoning_trace : JSON.stringify(d.reasoning_trace, null, 2)}
                </div>
              </div>
            )}

            {d.ambiguity_reason && (
              <div className="bg-amber-50 border border-amber-200 rounded-lg p-3">
                <label className="text-xs font-medium text-amber-700 uppercase tracking-wider">Ambiguity Reason</label>
                <p className="text-sm text-amber-800 mt-1">{d.ambiguity_reason}</p>
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
};

export default SourceDrawer;
