import React, { useEffect, useState } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import client from '../api/client';
import { TenderResults, Verdict } from '../types';
import VerdictGrid from '../components/VerdictGrid';
import SourceDrawer from '../components/SourceDrawer';

const Results: React.FC = () => {
  const { tenderId } = useParams<{ tenderId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [results, setResults] = useState<TenderResults | null>(null);
  const [processed, setProcessed] = useState(0);
  const [total, setTotal] = useState(0);
  const [polling, setPolling] = useState(searchParams.get('polling') === 'true');
  const [selectedVerdict, setSelectedVerdict] = useState<Verdict | null>(null);
  const [runningAnomaly, setRunningAnomaly] = useState(false);

  useEffect(() => {
    if (!tenderId || !polling) { loadResults(); return; }
    const interval = setInterval(async () => {
      try {
        const r = await client.get(`/api/evaluation/status/${tenderId}`);
        setProcessed(r.data.processed); setTotal(r.data.total);
        if (r.data.status === 'complete') { clearInterval(interval); setPolling(false); loadResults(); }
      } catch { clearInterval(interval); }
    }, 5000);
    return () => clearInterval(interval);
  }, [tenderId, polling]);

  const loadResults = async () => {
    if (!tenderId) return;
    try { const r = await client.get(`/api/evaluation/results/${tenderId}`); setResults(r.data); } catch (e) { console.error(e); }
  };

  const runAnomalyDetection = async () => {
    setRunningAnomaly(true);
    try { await client.post(`/api/credibility/anomalies/${tenderId}`); navigate(`/anomalies/${tenderId}`); } catch (e) { console.error(e); setRunningAnomaly(false); }
  };

  if (polling) return (
    <div className="max-w-3xl mx-auto px-4 py-20 text-center">
      <div className="animate-spin rounded-full h-16 w-16 border-4 border-indigo-200 border-t-indigo-600 mx-auto mb-6" />
      <h2 className="text-xl font-semibold text-slate-800">Computing Verdicts</h2>
      <p className="text-slate-500 mt-2">{processed} of {total} verdicts computed</p>
      <div className="mt-4 w-full bg-slate-200 rounded-full h-3"><div className="bg-indigo-600 h-3 rounded-full transition-all" style={{ width: `${total > 0 ? (processed / total) * 100 : 0}%` }} /></div>
    </div>
  );

  if (!results) return <div className="flex items-center justify-center min-h-[60vh]"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" /></div>;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <button onClick={() => navigate(`/criteria/${tenderId}`)} className="text-sm font-medium text-slate-500 hover:text-slate-800 mb-4 flex items-center gap-1">
        ← Back to Criteria
      </button>
      <div className="flex justify-between items-end mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Evaluation Results</h1>
          <p className="text-sm text-slate-500 mt-1">Tender: {tenderId} · {results.total_bidders} bidders · {results.total_criteria} criteria</p>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full">Step 3 of 5</span>
          <button onClick={runAnomalyDetection} disabled={runningAnomaly} className="px-5 py-2.5 bg-amber-600 text-white font-medium rounded-xl hover:bg-amber-700 transition-all disabled:opacity-50 active:scale-95">
            {runningAnomaly ? 'Detecting...' : 'Run Anomaly Detection →'}
          </button>
        </div>
      </div>
      <VerdictGrid bidders={results.bidders} criteria={results.criteria} onCellClick={setSelectedVerdict} />
      <SourceDrawer verdict={selectedVerdict} onClose={() => setSelectedVerdict(null)} />
    </div>
  );
};

export default Results;
