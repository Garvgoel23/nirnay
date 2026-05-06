import React from 'react';
import { Verdict, BidderVerdictGroup } from '../types';

interface VerdictGridProps {
  bidders: BidderVerdictGroup[];
  criteria: { criterion_id: string; description: string; type: string }[];
  onCellClick: (verdict: Verdict) => void;
}

const verdictColors: Record<string, string> = {
  ELIGIBLE: 'bg-emerald-100 text-emerald-800 border-emerald-200',
  NOT_ELIGIBLE: 'bg-red-100 text-red-800 border-red-200',
  MANUAL_REVIEW: 'bg-amber-100 text-amber-800 border-amber-200',
};

const overallColors: Record<string, string> = {
  ELIGIBLE: 'bg-emerald-600 text-white',
  NOT_ELIGIBLE: 'bg-red-600 text-white',
  MANUAL_REVIEW: 'bg-amber-500 text-white',
};

const VerdictGrid: React.FC<VerdictGridProps> = ({ bidders, criteria, onCellClick }) => {
  return (
    <div className="overflow-x-auto rounded-xl border border-slate-200 shadow-sm">
      <div className="min-w-[800px]">
        {/* Header row */}
        <div className="grid gap-px bg-slate-200" style={{ gridTemplateColumns: `200px 140px repeat(${criteria.length}, 120px)` }}>
          <div className="bg-slate-50 px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider">Bidder</div>
          <div className="bg-slate-50 px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wider sticky left-0 z-10">Overall</div>
          {criteria.map(c => (
            <div key={c.criterion_id} className="bg-slate-50 px-2 py-3 text-xs font-medium text-slate-600" title={c.description}>
              {c.criterion_id}
            </div>
          ))}
        </div>

        {/* Data rows */}
        {bidders.map(bidder => {
          const verdictMap: Record<string, Verdict> = {};
          bidder.criteria_verdicts.forEach(v => { verdictMap[v.criterion_id] = v; });

          return (
            <div key={bidder.bidder_id} className="grid gap-px bg-slate-200" style={{ gridTemplateColumns: `200px 140px repeat(${criteria.length}, 120px)` }}>
              <div className="bg-white px-3 py-3 text-sm font-medium text-slate-700 truncate">{bidder.bidder_id}</div>
              <div className={`${overallColors[bidder.overall_verdict]} px-3 py-3 text-sm font-semibold text-center sticky left-0 z-10`}>
                {bidder.overall_verdict.replace('_', ' ')}
              </div>
              {criteria.map(c => {
                const v = verdictMap[c.criterion_id];
                if (!v) return <div key={c.criterion_id} className="bg-slate-50 px-2 py-3 text-xs text-slate-400 text-center">—</div>;
                return (
                  <button key={c.criterion_id} onClick={() => onCellClick(v)}
                    className={`${verdictColors[v.verdict]} px-2 py-3 text-center border cursor-pointer hover:opacity-80 transition-opacity`}>
                    <div className="text-xs font-semibold">{v.verdict.replace('_', ' ')}</div>
                    <div className="text-[10px] mt-0.5 opacity-70">{(v.confidence_score * 100).toFixed(0)}%</div>
                  </button>
                );
              })}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default VerdictGrid;
