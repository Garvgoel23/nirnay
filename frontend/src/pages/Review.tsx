import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import client from '../api/client';
import { Verdict } from '../types';
import { useAuth } from '../context/AuthContext';
import ReviewCard from '../components/ReviewCard';

const Review: React.FC = () => {
  const { tenderId } = useParams<{ tenderId: string }>();
  const { role } = useAuth();
  const [verdicts, setVerdicts] = useState<Verdict[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(0);
  const [signingOff, setSigningOff] = useState(false);
  const [resolvedIds, setResolvedIds] = useState<Set<string>>(new Set());
  const perPage = 10;

  useEffect(() => {
    if (!tenderId) return;
    client.get(`/api/review/queue/${tenderId}`).then(r => setVerdicts(r.data.verdicts || [])).catch(console.error).finally(() => setLoading(false));
  }, [tenderId]);

  const handleResolved = (verdictId: string) => { setResolvedIds(prev => new Set(prev).add(verdictId)); };

  const handleSignOff = async () => {
    setSigningOff(true);
    try { await client.post(`/api/review/signoff/${tenderId}`); alert('Tender signed off successfully'); } catch (e: any) { alert(e.response?.data?.detail || 'Sign-off failed'); }
    setSigningOff(false);
  };

  const paged = verdicts.slice(page * perPage, (page + 1) * perPage);
  const totalPages = Math.ceil(verdicts.length / perPage);
  const allPageResolved = paged.every(v => resolvedIds.has(v.verdict_id));
  const pendingCount = verdicts.filter(v => !resolvedIds.has(v.verdict_id)).length;

  if (loading) return <div className="flex items-center justify-center min-h-[60vh]"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" /></div>;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-6">
        <div><h1 className="text-2xl font-bold text-slate-900">Manual Review Queue</h1><p className="text-sm text-slate-500 mt-1">Tender: {tenderId} · {verdicts.length} items</p></div>
        {role === 'senior_officer' && (
          <button onClick={handleSignOff} disabled={pendingCount > 0 || signingOff}
            className="px-5 py-2.5 bg-emerald-600 text-white font-medium rounded-xl hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-95">
            {signingOff ? 'Signing Off...' : `Sign Off Tender${pendingCount > 0 ? ` (${pendingCount} pending)` : ''}`}
          </button>
        )}
      </div>

      {verdicts.length === 0 ? (
        <div className="text-center py-16"><p className="text-lg text-slate-400">No manual reviews pending</p>
          <Link to={`/export/${tenderId}`} className="mt-4 inline-block px-5 py-2.5 bg-indigo-600 text-white font-medium rounded-xl">Proceed to Export →</Link></div>
      ) : (
        <>
          <div className="space-y-4 mb-6">
            {paged.map(v => <ReviewCard key={v.verdict_id} verdict={v} onResolved={handleResolved} />)}
          </div>

          {totalPages > 1 && (
            <div className="flex justify-center gap-2">
              <button onClick={() => setPage(p => Math.max(0, p - 1))} disabled={page === 0} className="px-4 py-2 text-sm border border-slate-300 rounded-lg disabled:opacity-50">Previous</button>
              <span className="px-4 py-2 text-sm text-slate-500">Page {page + 1} of {totalPages}</span>
              <button onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))} disabled={page >= totalPages - 1} className="px-4 py-2 text-sm border border-slate-300 rounded-lg disabled:opacity-50">Next</button>
            </div>
          )}

          {allPageResolved && <div className="text-center mt-6"><Link to={`/export/${tenderId}`} className="px-5 py-2.5 bg-indigo-600 text-white font-medium rounded-xl hover:bg-indigo-700 transition-all">Proceed to Export →</Link></div>}
        </>
      )}
    </div>
  );
};

export default Review;
