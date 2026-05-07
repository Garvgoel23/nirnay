import React, { useEffect, useState } from 'react';
import { useParams, useSearchParams, useNavigate } from 'react-router-dom';
import client from '../api/client';
import { TenderResults, Verdict, BidderVerdictGroup } from '../types';
import VerdictGrid from '../components/VerdictGrid';
import SourceDrawer from '../components/SourceDrawer';
import { useAuth } from '../context/AuthContext';

const Results: React.FC = () => {
  const { tenderId } = useParams<{ tenderId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { role } = useAuth();
  const [results, setResults] = useState<TenderResults | null>(null);
  const [processed, setProcessed] = useState(0);
  const [total, setTotal] = useState(0);
  const [polling, setPolling] = useState(searchParams.get('polling') === 'true');
  const [selectedVerdict, setSelectedVerdict] = useState<Verdict | null>(null);
  const [runningAnomaly, setRunningAnomaly] = useState(false);
  const [signingOff, setSigningOff] = useState(false);

  useEffect(() => {
    if (!tenderId || !polling) { loadResults(); return; }
    const interval = setInterval(async () => {
      try {
        const r = await client.get(`/api/evaluation/status/${tenderId}`);
        setProcessed(r.data.processed);
        setTotal(r.data.total);
        if (r.data.status === 'complete') {
          clearInterval(interval);
          setPolling(false);
          loadResults();
        }
      } catch { clearInterval(interval); }
    }, 3000);
    return () => clearInterval(interval);
  }, [tenderId, polling]);

  const loadResults = async () => {
    if (!tenderId) return;
    try {
      const r = await client.get(`/api/evaluation/results/${tenderId}`);
      setResults(r.data);
    } catch (e) { console.error(e); }
  };

  const runAnomalyDetection = async () => {
    setRunningAnomaly(true);
    try {
      await client.post(`/api/credibility/anomalies/${tenderId}`);
      navigate(`/anomalies/${tenderId}`);
    } catch (e) { console.error(e); setRunningAnomaly(false); }
  };

  const handleSignOff = async () => {
    if (!window.confirm('Sign off this tender? This confirms the evaluation is complete.')) return;
    setSigningOff(true);
    try {
      await client.post(`/api/review/signoff/${tenderId}`);
      navigate(`/export/${tenderId}`);
    } catch (e: any) {
      alert(e.response?.data?.detail || 'Sign-off failed');
      setSigningOff(false);
    }
  };

  /* ── Polling screen ── */
  if (polling) {
    const pct = total > 0 ? Math.round((processed / total) * 100) : 0;
    return (
      <div className="max-w-3xl mx-auto px-4 py-20 text-center">
        <div className="animate-spin rounded-full h-16 w-16 border-4 border-indigo-200 border-t-indigo-600 mx-auto mb-6" />
        <h2 className="text-xl font-semibold text-slate-800">Computing Verdicts</h2>
        {total === 0 ? (
          <p className="text-slate-500 mt-2">Starting evaluation engine…</p>
        ) : (
          <p className="text-slate-500 mt-2">{processed} of {total} verdicts computed</p>
        )}
        <div className="mt-4 w-full bg-slate-200 rounded-full h-3">
          <div
            className="bg-indigo-600 h-3 rounded-full transition-all duration-500"
            style={{ width: `${pct}%` }}
          />
        </div>
        {total > 0 && (
          <p className="text-xs text-slate-400 mt-2">{pct}% complete</p>
        )}
      </div>
    );
  }

  if (!results) return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" />
    </div>
  );

  /* ── Summary stats ── */
  const eligible = results.bidders.filter(b => b.overall_verdict === 'ELIGIBLE').length;
  const notEligible = results.bidders.filter(b => b.overall_verdict === 'NOT_ELIGIBLE').length;
  const manualReview = results.bidders.filter(b => b.overall_verdict === 'MANUAL_REVIEW').length;
  const allResolved = manualReview === 0;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <button onClick={() => navigate(`/criteria/${tenderId}`)} className="text-sm font-medium text-slate-500 hover:text-slate-800 mb-4 flex items-center gap-1">
        ← Back to Criteria
      </button>

      {/* Page header */}
      <div className="flex justify-between items-end mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Evaluation Results</h1>
          <p className="text-sm text-slate-500 mt-1">
            Tender: {tenderId} · {results.total_bidders} bidders · {results.total_criteria} criteria
          </p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full">Step 3 of 5</span>
          <button
            onClick={() => navigate(`/compare/${tenderId}`)}
            className="px-4 py-2 text-sm font-medium text-slate-700 border border-slate-300 rounded-xl hover:bg-slate-50 transition-all"
          >
            ⚖ Compare Bids
          </button>
          <button
            onClick={runAnomalyDetection}
            disabled={runningAnomaly}
            className="px-5 py-2.5 bg-amber-600 text-white font-medium rounded-xl hover:bg-amber-700 transition-all disabled:opacity-50 active:scale-95"
          >
            {runningAnomaly ? 'Detecting…' : 'Run Anomaly Detection →'}
          </button>
        </div>
      </div>

      {/* Verdict grid */}
      <VerdictGrid bidders={results.bidders} criteria={results.criteria} onCellClick={setSelectedVerdict} />

      {/* ── Decision Panel ── */}
      <div className="mt-8 bg-white rounded-2xl border border-slate-200 shadow-sm p-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Officer Decision Panel</h2>

        {/* Summary cards */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="bg-emerald-50 rounded-xl p-4 text-center border border-emerald-100">
            <p className="text-3xl font-bold text-emerald-700">{eligible}</p>
            <p className="text-sm text-emerald-600 mt-1">Eligible</p>
          </div>
          <div className="bg-red-50 rounded-xl p-4 text-center border border-red-100">
            <p className="text-3xl font-bold text-red-700">{notEligible}</p>
            <p className="text-sm text-red-600 mt-1">Not Eligible</p>
          </div>
          <div className="bg-amber-50 rounded-xl p-4 text-center border border-amber-100">
            <p className="text-3xl font-bold text-amber-700">{manualReview}</p>
            <p className="text-sm text-amber-600 mt-1">Pending Review</p>
          </div>
        </div>

        {/* Action buttons */}
        <div className="flex flex-wrap gap-3">
          {manualReview > 0 && (
            <button
              onClick={() => navigate(`/review/${tenderId}`)}
              className="px-5 py-2.5 bg-indigo-600 text-white font-medium rounded-xl hover:bg-indigo-700 transition-all active:scale-95"
            >
              Proceed to Manual Review ({manualReview} items) →
            </button>
          )}

          {allResolved && (
            <>
              <button
                onClick={() => navigate(`/review/${tenderId}`)}
                className="px-5 py-2.5 border border-slate-300 text-slate-700 font-medium rounded-xl hover:bg-slate-50 transition-all"
              >
                View Review Queue
              </button>
              {role === 'senior_officer' && (
                <button
                  onClick={handleSignOff}
                  disabled={signingOff}
                  className="px-5 py-2.5 bg-emerald-600 text-white font-medium rounded-xl hover:bg-emerald-700 transition-all disabled:opacity-50 active:scale-95"
                >
                  {signingOff ? 'Signing Off…' : '✓ Sign Off & Proceed to Export'}
                </button>
              )}
            </>
          )}
        </div>

        {allResolved && role !== 'senior_officer' && (
          <p className="text-xs text-slate-400 mt-3">Sign-off requires senior officer role. All manual reviews have been resolved.</p>
        )}
      </div>

      <SourceDrawer verdict={selectedVerdict} onClose={() => setSelectedVerdict(null)} />
    </div>
  );
};

export default Results;
