import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import client from '../api/client';
import { Criterion, Contradiction } from '../types';

const typeBadge: Record<string, string> = { financial: 'bg-blue-100 text-blue-700', technical: 'bg-purple-100 text-purple-700', compliance: 'bg-emerald-100 text-emerald-700', documentation: 'bg-slate-100 text-slate-600' };

const Criteria: React.FC = () => {
  const { tenderId } = useParams<{ tenderId: string }>();
  const navigate = useNavigate();
  const [criteria, setCriteria] = useState<Criterion[]>([]);
  const [contradictions, setContradictions] = useState<Contradiction[]>([]);
  const [loading, setLoading] = useState(true);
  const [showContradictions, setShowContradictions] = useState(true);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    if (!tenderId) return;
    Promise.all([
      client.get(`/api/extraction/criteria/${tenderId}`),
      client.post(`/api/credibility/contradictions/${tenderId}`),
    ]).then(([cr, co]) => { setCriteria(cr.data.criteria || []); setContradictions(co.data.contradictions || []); }).catch(console.error).finally(() => setLoading(false));
  }, [tenderId]);

  const runEvaluation = async () => {
    setRunning(true);
    try { await client.post(`/api/evaluation/run/${tenderId}`); navigate(`/results/${tenderId}?polling=true`); } catch (e) { console.error(e); setRunning(false); }
  };

  if (loading) return <div className="flex items-center justify-center min-h-[60vh]"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" /></div>;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-6">
        <div><h1 className="text-2xl font-bold text-slate-900">Criteria Review</h1><p className="text-sm text-slate-500 mt-1">Tender: {tenderId}</p></div>
        <button onClick={runEvaluation} disabled={running} className="px-5 py-2.5 bg-indigo-600 text-white font-medium rounded-xl hover:bg-indigo-700 transition-all disabled:opacity-50 active:scale-95">
          {running ? 'Starting...' : 'Run Evaluation'}
        </button>
      </div>

      {contradictions.length > 0 && (
        <div className="mb-6 bg-amber-50 border border-amber-200 rounded-xl p-4">
          <button onClick={() => setShowContradictions(!showContradictions)} className="flex justify-between items-center w-full">
            <h3 className="font-semibold text-amber-900">⚠️ Contradiction Warning ({contradictions.length})</h3>
            <span className="text-amber-600 text-sm">{showContradictions ? 'Hide' : 'Show'}</span>
          </button>
          {showContradictions && (
            <div className="mt-3 space-y-3">
              {contradictions.map((c, i) => (
                <div key={i} className="bg-white rounded-lg p-3 border border-amber-100">
                  <div className="flex gap-2 mb-2">
                    <span className="px-2 py-0.5 text-xs font-medium bg-slate-100 rounded-full">{c.contradiction_type}</span>
                    <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${c.severity === 'error' ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}`}>{c.severity}</span>
                  </div>
                  <p className="text-sm text-slate-700">{c.description}</p>
                  {c.suggested_resolution && <p className="text-xs text-slate-500 mt-1 italic">Suggestion: {c.suggested_resolution}</p>}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead><tr className="bg-slate-50 border-b border-slate-200">
            <th className="text-left px-4 py-3 text-xs font-medium text-slate-400 uppercase">ID</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-slate-400 uppercase">Type</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-slate-400 uppercase">Description</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-slate-400 uppercase">Threshold</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-slate-400 uppercase">Mandatory</th>
          </tr></thead>
          <tbody>
            {criteria.map(c => (
              <tr key={c.criterion_id} className="border-b border-slate-50 hover:bg-slate-50 transition-colors">
                <td className="px-4 py-3 font-mono text-xs text-slate-600">{c.criterion_id}</td>
                <td className="px-4 py-3"><span className={`px-2 py-0.5 text-xs font-medium rounded-full ${typeBadge[c.type] || ''}`}>{c.type}</span></td>
                <td className="px-4 py-3 text-slate-700 max-w-md">{c.description}</td>
                <td className="px-4 py-3 text-slate-600">{c.threshold_value ? `${c.threshold_value} ${c.threshold_unit || ''}` : '—'}</td>
                <td className="px-4 py-3">{c.mandatory ? <span className="px-2 py-0.5 text-xs font-medium bg-emerald-100 text-emerald-700 rounded-full">Yes</span> : <span className="px-2 py-0.5 text-xs font-medium bg-slate-100 text-slate-500 rounded-full">No</span>}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Criteria;
