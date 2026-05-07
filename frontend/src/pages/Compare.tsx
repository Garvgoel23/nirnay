import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import client from '../api/client';
import { TenderResults, BidderVerdictGroup, Verdict } from '../types';

const verdictConfig = {
  ELIGIBLE:      { bg: 'bg-emerald-50',  text: 'text-emerald-700', border: 'border-emerald-200', badge: 'bg-emerald-100 text-emerald-700', icon: '✓' },
  NOT_ELIGIBLE:  { bg: 'bg-red-50',      text: 'text-red-700',     border: 'border-red-200',     badge: 'bg-red-100 text-red-700',       icon: '✗' },
  MANUAL_REVIEW: { bg: 'bg-amber-50',    text: 'text-amber-700',   border: 'border-amber-200',   badge: 'bg-amber-100 text-amber-700',   icon: '?' },
};

const typeBadge: Record<string, string> = {
  financial:     'bg-blue-100 text-blue-700',
  technical:     'bg-purple-100 text-purple-700',
  compliance:    'bg-emerald-100 text-emerald-700',
  documentation: 'bg-slate-100 text-slate-600',
};

const Compare: React.FC = () => {
  const { tenderId } = useParams<{ tenderId: string }>();
  const navigate = useNavigate();
  const [data, setData] = useState<TenderResults | null>(null);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!tenderId) return;
    client.get(`/api/evaluation/results/${tenderId}`)
      .then(r => {
        setData(r.data);
        // Default: select all bidders (up to 4)
        const ids = (r.data.bidders || []).slice(0, 4).map((b: BidderVerdictGroup) => b.bidder_id);
        setSelected(new Set(ids));
      })
      .catch(console.error)
      .finally(() => setLoading(false));
  }, [tenderId]);

  const toggleBidder = (id: string) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(id)) { next.delete(id); } else { next.add(id); }
      return next;
    });
  };

  if (loading) return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" />
    </div>
  );

  if (!data) return (
    <div className="max-w-3xl mx-auto py-20 text-center text-slate-400">No evaluation data found.</div>
  );

  const activeBidders = data.bidders.filter(b => selected.has(b.bidder_id));

  const getVerdict = (bidder: BidderVerdictGroup, criterionId: string): Verdict | undefined =>
    bidder.criteria_verdicts.find(v => v.criterion_id === criterionId);

  const overallScore = (bidder: BidderVerdictGroup): number => {
    const vs = bidder.criteria_verdicts;
    if (!vs.length) return 0;
    const pts = vs.reduce((acc, v) => {
      if (v.verdict === 'ELIGIBLE') return acc + 100;
      if (v.verdict === 'NOT_ELIGIBLE') return acc;
      return acc + 50; // MANUAL_REVIEW
    }, 0);
    return Math.round(pts / vs.length);
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <button onClick={() => navigate(`/results/${tenderId}`)} className="text-sm font-medium text-slate-500 hover:text-slate-800 mb-4 flex items-center gap-1">
        ← Back to Results
      </button>
      <div className="flex justify-between items-end mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Bid Comparison</h1>
          <p className="text-sm text-slate-500 mt-1">Tender: {tenderId} · {data.total_criteria} criteria · {data.total_bidders} bidders</p>
        </div>
      </div>

      {/* Bidder selector */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 mb-6">
        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3">Select Bidders to Compare</p>
        <div className="flex flex-wrap gap-2">
          {data.bidders.map(b => {
            const cfg = verdictConfig[b.overall_verdict];
            const isActive = selected.has(b.bidder_id);
            return (
              <button
                key={b.bidder_id}
                onClick={() => toggleBidder(b.bidder_id)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium border transition-all ${
                  isActive
                    ? `${cfg.bg} ${cfg.text} ${cfg.border} shadow-sm`
                    : 'bg-slate-50 text-slate-400 border-slate-200 hover:border-slate-300'
                }`}
              >
                {isActive ? '✓ ' : ''}{b.bidder_id}
                <span className={`ml-2 text-xs px-1.5 py-0.5 rounded-full ${cfg.badge}`}>
                  {b.overall_verdict.replace('_', ' ')}
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {activeBidders.length === 0 ? (
        <div className="py-16 text-center text-slate-400">Select at least one bidder to compare.</div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                {/* Overall row */}
                <tr className="border-b-2 border-slate-200 bg-slate-900">
                  <th className="text-left px-4 py-4 text-xs font-semibold text-slate-300 uppercase tracking-wider w-80">
                    Criterion
                  </th>
                  {activeBidders.map(b => {
                    const cfg = verdictConfig[b.overall_verdict];
                    const score = overallScore(b);
                    return (
                      <th key={b.bidder_id} className="px-4 py-4 text-center min-w-[160px]">
                        <div className="text-white font-semibold text-sm">{b.bidder_id}</div>
                        <div className={`mt-1 inline-block px-2 py-0.5 rounded-full text-xs font-bold ${cfg.badge}`}>
                          {b.overall_verdict.replace('_', ' ')}
                        </div>
                        <div className="mt-2">
                          <div className="text-xs text-slate-400 mb-1">Overall Score</div>
                          <div className="w-full bg-slate-700 rounded-full h-2 mx-auto">
                            <div
                              className={`h-2 rounded-full ${score >= 70 ? 'bg-emerald-400' : score >= 40 ? 'bg-amber-400' : 'bg-red-400'}`}
                              style={{ width: `${score}%` }}
                            />
                          </div>
                          <div className="text-xs font-bold text-slate-300 mt-1">{score}%</div>
                        </div>
                      </th>
                    );
                  })}
                </tr>
              </thead>

              <tbody>
                {data.criteria.map((c, idx) => (
                  <tr key={c.criterion_id} className={idx % 2 === 0 ? 'bg-white' : 'bg-slate-50'}>
                    {/* Criterion cell */}
                    <td className="px-4 py-3 border-r border-slate-100">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`px-1.5 py-0.5 text-xs font-medium rounded-full ${typeBadge[c.type] || 'bg-slate-100 text-slate-500'}`}>
                          {c.type}
                        </span>
                        <span className="font-mono text-xs text-slate-400">{c.criterion_id}</span>
                      </div>
                      <p className="text-sm text-slate-700 font-medium leading-snug">{c.description}</p>
                    </td>

                    {/* Verdict cells per bidder */}
                    {activeBidders.map(b => {
                      const v = getVerdict(b, c.criterion_id);
                      if (!v) return (
                        <td key={b.bidder_id} className="px-4 py-3 text-center text-slate-300 text-xs border-r border-slate-100">—</td>
                      );
                      const cfg = verdictConfig[v.verdict];
                      return (
                        <td key={b.bidder_id} className={`px-3 py-3 border-r border-slate-100 ${cfg.bg}`}>
                          <div className="flex items-center justify-center gap-1 mb-1">
                            <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${cfg.badge}`}>
                              {cfg.icon} {v.verdict.replace('_', ' ')}
                            </span>
                          </div>
                          {v.extracted_value && (
                            <p className="text-xs text-center text-slate-600 truncate max-w-[130px] mx-auto" title={v.extracted_value}>
                              {v.extracted_value}
                            </p>
                          )}
                          <div className="mt-1.5 flex items-center justify-center gap-1">
                            <div className="w-12 bg-slate-200 rounded-full h-1.5">
                              <div
                                className={`h-1.5 rounded-full ${v.confidence_score >= 0.75 ? 'bg-emerald-500' : v.confidence_score >= 0.5 ? 'bg-amber-500' : 'bg-red-500'}`}
                                style={{ width: `${v.confidence_score * 100}%` }}
                              />
                            </div>
                            <span className="text-[10px] text-slate-400">{(v.confidence_score * 100).toFixed(0)}%</span>
                          </div>
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default Compare;
