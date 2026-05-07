import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import client from '../api/client';

interface Letter {
  bidder_id: string;
  letter_text: string;
  failing_criteria?: string[];
}

const Export: React.FC = () => {
  const { tenderId } = useParams<{ tenderId: string }>();
  const navigate = useNavigate();
  const [letters, setLetters] = useState<Record<string, string>>({});
  const [failingMap, setFailingMap] = useState<Record<string, string[]>>({});
  const [loadingLetters, setLoadingLetters] = useState(false);
  const [generatingReport, setGeneratingReport] = useState(false);
  const [generatingAudit, setGeneratingAudit] = useState(false);
  const [hasRejected, setHasRejected] = useState<boolean | null>(null);

  /* Auto-draft all letters on page load */
  useEffect(() => {
    if (!tenderId) return;
    setLoadingLetters(true);
    client.post(`/api/notification/draft-all-letters/${tenderId}`)
      .then(r => {
        const result: Letter[] = r.data.letters || [];
        const lMap: Record<string, string> = {};
        const fMap: Record<string, string[]> = {};
        result.forEach(l => {
          lMap[l.bidder_id] = l.letter_text;
          fMap[l.bidder_id] = l.failing_criteria || [];
        });
        setLetters(lMap);
        setFailingMap(fMap);
        setHasRejected(result.length > 0);
      })
      .catch(e => {
        console.error('Failed to load rejection letters:', e);
        setHasRejected(false);
      })
      .finally(() => setLoadingLetters(false));
  }, [tenderId]);

  const downloadBlob = (data: Blob, filename: string) => {
    const url = URL.createObjectURL(data);
    const a = document.createElement('a');
    a.href = url; a.download = filename; a.click();
    URL.revokeObjectURL(url);
  };

  const generateReport = async () => {
    setGeneratingReport(true);
    try {
      const r = await client.post(`/api/notification/report/${tenderId}`, {}, { responseType: 'blob' });
      downloadBlob(r.data, `nirnay_report_${tenderId}.pdf`);
    } catch (e) { console.error(e); }
    finally { setGeneratingReport(false); }
  };

  const generateAudit = async () => {
    setGeneratingAudit(true);
    try {
      const r = await client.post(`/api/notification/audit/${tenderId}`, {}, { responseType: 'blob' });
      downloadBlob(r.data, `nirnay_audit_${tenderId}.pdf`);
    } catch (e) { console.error(e); }
    finally { setGeneratingAudit(false); }
  };

  const downloadLetter = (bidderId: string) => {
    const text = letters[bidderId];
    if (!text) return;
    const blob = new Blob([text], { type: 'text/plain' });
    downloadBlob(blob, `${bidderId}_rejection_${tenderId}.txt`);
  };

  const rejectedBidders = Object.keys(letters);

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <button onClick={() => navigate(`/review/${tenderId}`)} className="text-sm font-medium text-slate-500 hover:text-slate-800 mb-4 flex items-center gap-1">
        ← Back to Review
      </button>

      <div className="flex justify-between items-end mb-8">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Export & Finalise</h1>
          <p className="text-sm text-slate-500 mt-1">Tender: {tenderId}</p>
        </div>
        <span className="text-sm font-medium text-emerald-600 bg-emerald-50 px-3 py-1 rounded-full">Step 5 of 5 — Completed</span>
      </div>

      {/* Evaluation Report */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 mb-5">
        <h2 className="text-lg font-semibold text-slate-800">Evaluation Report</h2>
        <p className="text-sm text-slate-500 mt-1 mb-4">
          Full PDF including per-bidder verdict tables with AI reasoning, full criteria descriptions, anomaly summary, and SHA-256 integrity hash.
        </p>
        <button onClick={generateReport} disabled={generatingReport}
          className="px-5 py-2.5 bg-indigo-600 text-white font-medium rounded-xl hover:bg-indigo-700 disabled:opacity-50 transition-all active:scale-95 flex items-center gap-2">
          {generatingReport && <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />}
          {generatingReport ? 'Generating…' : '⬇ Download Evaluation Report (PDF)'}
        </button>
      </div>

      {/* Audit Export */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 mb-5">
        <h2 className="text-lg font-semibold text-slate-800">Audit Trail Export</h2>
        <p className="text-sm text-slate-500 mt-1 mb-4">
          Complete audit trail with all LLM calls, officer override actions, verdict chain, and SHA-256 hash for regulatory compliance.
        </p>
        <button onClick={generateAudit} disabled={generatingAudit}
          className="px-5 py-2.5 bg-indigo-600 text-white font-medium rounded-xl hover:bg-indigo-700 disabled:opacity-50 transition-all active:scale-95 flex items-center gap-2">
          {generatingAudit && <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />}
          {generatingAudit ? 'Generating…' : '⬇ Download Audit Export (PDF)'}
        </button>
      </div>

      {/* Rejection Letters */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-semibold text-slate-800">Rejection Letters</h2>
            <p className="text-sm text-slate-500 mt-0.5">Auto-generated GoI-format letters for all not-eligible bidders.</p>
          </div>
          {loadingLetters && (
            <div className="flex items-center gap-2 text-sm text-slate-500">
              <span className="w-4 h-4 border-2 border-slate-400 border-t-transparent rounded-full animate-spin" />
              Generating letters…
            </div>
          )}
        </div>

        {hasRejected === false && !loadingLetters && (
          <div className="py-6 text-center">
            <div className="text-3xl mb-2">🎉</div>
            <p className="text-slate-500 font-medium">No rejected bidders for this tender.</p>
            <p className="text-sm text-slate-400 mt-1">All bidders are eligible or pending review.</p>
          </div>
        )}

        {rejectedBidders.length > 0 && (
          <div className="space-y-5">
            {rejectedBidders.map(bidderId => (
              <div key={bidderId} className="border border-slate-200 rounded-xl p-4">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <span className="font-semibold text-slate-800">{bidderId}</span>
                    {failingMap[bidderId]?.length > 0 && (
                      <p className="text-xs text-slate-400 mt-0.5">
                        Failed: {failingMap[bidderId].join(', ')}
                      </p>
                    )}
                  </div>
                  <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs font-medium rounded-full">NOT ELIGIBLE</span>
                </div>

                <textarea
                  value={letters[bidderId] || ''}
                  onChange={e => setLetters(prev => ({ ...prev, [bidderId]: e.target.value }))}
                  className="w-full h-52 p-3 border border-slate-300 rounded-lg text-sm font-mono resize-y focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-slate-50"
                  placeholder="Generating letter…"
                />
                <div className="flex gap-2 mt-2">
                  <button onClick={() => downloadLetter(bidderId)}
                    className="px-4 py-1.5 text-sm bg-slate-700 text-white rounded-lg hover:bg-slate-800 transition-colors">
                    ⬇ Download .txt
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Export;
