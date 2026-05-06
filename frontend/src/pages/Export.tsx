import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import client from '../api/client';

const Export: React.FC = () => {
  const { tenderId } = useParams<{ tenderId: string }>();
  const [rejectedBidders, setRejectedBidders] = useState<{ bidder_id: string }[]>([]);
  const [letterTexts, setLetterTexts] = useState<Record<string, string>>({});
  const [generatingReport, setGeneratingReport] = useState(false);
  const [generatingAudit, setGeneratingAudit] = useState(false);
  const [draftingLetter, setDraftingLetter] = useState<string | null>(null);

  useEffect(() => {
    if (!tenderId) return;
    client.get(`/api/notification/rejected-bidders/${tenderId}`).then(r => setRejectedBidders(r.data.bidders || [])).catch(console.error);
  }, [tenderId]);

  const downloadBlob = (data: Blob, filename: string) => {
    const url = URL.createObjectURL(data);
    const a = document.createElement('a'); a.href = url; a.download = filename; a.click();
    URL.revokeObjectURL(url);
  };

  const generateReport = async () => {
    setGeneratingReport(true);
    try {
      const r = await client.post(`/api/notification/report/${tenderId}`, {}, { responseType: 'blob' });
      downloadBlob(r.data, `nirnay_report_${tenderId}.pdf`);
    } catch (e) { console.error(e); } finally { setGeneratingReport(false); }
  };

  const generateAudit = async () => {
    setGeneratingAudit(true);
    try {
      const r = await client.post(`/api/notification/audit/${tenderId}`, {}, { responseType: 'blob' });
      downloadBlob(r.data, `nirnay_audit_${tenderId}.pdf`);
    } catch (e) { console.error(e); } finally { setGeneratingAudit(false); }
  };

  const draftLetter = async (bidderId: string) => {
    setDraftingLetter(bidderId);
    try {
      const r = await client.post(`/api/notification/draft-letter/${bidderId}?tender_id=${tenderId}`);
      setLetterTexts(prev => ({ ...prev, [bidderId]: r.data.letter_text }));
    } catch (e) { console.error(e); } finally { setDraftingLetter(null); }
  };

  const downloadLetter = (bidderId: string) => {
    const text = letterTexts[bidderId];
    if (!text) return;
    const blob = new Blob([text], { type: 'text/plain' });
    downloadBlob(blob, `${bidderId}_rejection_${tenderId}.txt`);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-slate-900 mb-8">Export</h1>

      {/* Evaluation Report */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800">Evaluation Report</h2>
        <p className="text-sm text-slate-500 mt-1">A full PDF report including per-bidder verdict tables, anomaly summary, and SHA-256 integrity hash.</p>
        <button onClick={generateReport} disabled={generatingReport} className="mt-4 px-5 py-2.5 bg-indigo-600 text-white font-medium rounded-xl hover:bg-indigo-700 disabled:opacity-50 transition-all active:scale-95 flex items-center gap-2">
          {generatingReport && <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />}
          {generatingReport ? 'Generating...' : 'Generate Evaluation Report'}
        </button>
      </div>

      <hr className="border-slate-200 my-6" />

      {/* Audit Export */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 mb-6">
        <h2 className="text-lg font-semibold text-slate-800">Audit Export</h2>
        <p className="text-sm text-slate-500 mt-1">A complete audit trail including all LLM calls, officer actions, and verdict chain, with SHA-256 hash.</p>
        <button onClick={generateAudit} disabled={generatingAudit} className="mt-4 px-5 py-2.5 bg-indigo-600 text-white font-medium rounded-xl hover:bg-indigo-700 disabled:opacity-50 transition-all active:scale-95 flex items-center gap-2">
          {generatingAudit && <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />}
          {generatingAudit ? 'Generating...' : 'Generate Audit Export'}
        </button>
      </div>

      <hr className="border-slate-200 my-6" />

      {/* Rejection Letters */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Rejection Letters</h2>
        {rejectedBidders.length === 0 ? (
          <p className="text-slate-400 text-sm py-4">No rejected bidders for this tender.</p>
        ) : (
          <div className="space-y-4">
            {rejectedBidders.map(b => (
              <div key={b.bidder_id} className="border border-slate-200 rounded-xl p-4">
                <div className="flex justify-between items-center">
                  <span className="font-medium text-slate-700">{b.bidder_id}</span>
                  <button onClick={() => draftLetter(b.bidder_id)} disabled={draftingLetter === b.bidder_id}
                    className="px-4 py-1.5 text-sm bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 disabled:opacity-50 transition-colors flex items-center gap-1.5">
                    {draftingLetter === b.bidder_id && <span className="w-3 h-3 border-2 border-slate-500 border-t-transparent rounded-full animate-spin" />}
                    {draftingLetter === b.bidder_id ? 'Drafting...' : 'Draft Letter'}
                  </button>
                </div>
                {letterTexts[b.bidder_id] && (
                  <div className="mt-3">
                    <textarea value={letterTexts[b.bidder_id]} onChange={e => setLetterTexts(prev => ({ ...prev, [b.bidder_id]: e.target.value }))}
                      className="w-full h-48 p-3 border border-slate-300 rounded-lg text-sm font-mono resize-y focus:outline-none focus:ring-2 focus:ring-indigo-500" />
                    <button onClick={() => downloadLetter(b.bidder_id)} className="mt-2 px-4 py-1.5 text-sm bg-emerald-100 text-emerald-700 rounded-lg hover:bg-emerald-200 transition-colors">Download as .txt</button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Export;
