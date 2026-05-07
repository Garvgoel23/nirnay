import React, { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import client from '../api/client';
import { DocumentStatus } from '../types';

interface FileEntry { file: File; bidderId: string; docId?: string; status: DocumentStatus | null; error?: string; }

const Upload: React.FC = () => {
  const navigate = useNavigate();
  const [departmentId, setDepartmentId] = useState('');
  const [tenderId, setTenderId] = useState('');
  const [tenderFile, setTenderFile] = useState<File | null>(null);
  const [tenderStatus, setTenderStatus] = useState<DocumentStatus | null>(null);
  const [bidderFiles, setBidderFiles] = useState<FileEntry[]>([]);
  const [uploading, setUploading] = useState(false);
  const [tenderDragActive, setTenderDragActive] = useState(false);
  const [bidderDragActive, setBidderDragActive] = useState(false);

  const ALLOWED = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'image/png', 'image/jpeg', 'image/tiff'];

  const pollStatus = useCallback(async (docId: string, setter: (s: DocumentStatus) => void) => {
    // Fire immediately so the first status shows without waiting
    const doFetch = async () => {
      try {
        const r = await client.get(`/api/ingestion/status/${docId}`);
        setter(r.data);
        if (['extracted', 'error'].includes(r.data.status)) {
          clearInterval(interval);
        }
      } catch { clearInterval(interval); }
    };
    doFetch(); // immediate first call — no 1.5s wait
    const interval = setInterval(doFetch, 1500); // poll every 1.5s (was 3s)
  }, []);

  const handleUpload = async () => {
    if (!tenderFile || !departmentId || !tenderId) return;
    setUploading(true);

    // Upload tender
    const tenderForm = new FormData();
    tenderForm.append('file', tenderFile);
    tenderForm.append('department_id', departmentId);
    tenderForm.append('tender_id', tenderId);
    try {
      const r = await client.post('/api/ingestion/tender', tenderForm, { headers: { 'Content-Type': 'multipart/form-data' } });
      pollStatus(r.data.doc_id, setTenderStatus);
    } catch (e: any) { console.error('Tender upload failed:', e); }

    // Upload bidder files sequentially
    for (let i = 0; i < bidderFiles.length; i++) {
      const entry = bidderFiles[i];
      if (!entry.bidderId) continue;
      const form = new FormData();
      form.append('file', entry.file);
      form.append('department_id', departmentId);
      form.append('tender_id', tenderId);
      form.append('bidder_id', entry.bidderId);
      try {
        const r = await client.post('/api/ingestion/bidder', form, { headers: { 'Content-Type': 'multipart/form-data' } });
        const docId = r.data.doc_id;
        const idx = i;
        pollStatus(docId, (s) => {
          setBidderFiles(prev => { const n = [...prev]; n[idx] = { ...n[idx], status: s, docId }; return n; });
        });
      } catch (e: any) { console.error(`Bidder upload ${i} failed:`, e); }
    }
    setUploading(false);
  };

  const statusChip = (status: string | undefined) => {
    const styles: Record<string, string> = {
      uploaded: 'bg-slate-100 text-slate-600', ocr_processing: 'bg-blue-100 text-blue-700', ocr_complete: 'bg-blue-50 text-blue-600',
      extracting: 'bg-indigo-100 text-indigo-700', extracted: 'bg-emerald-100 text-emerald-700', error: 'bg-red-100 text-red-700',
    };
    const spinning = ['ocr_processing', 'extracting'].includes(status || '');
    return (
      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-full ${styles[status || ''] || 'bg-slate-100 text-slate-500'}`}>
        {spinning && <span className="w-3 h-3 border-2 border-current border-t-transparent rounded-full animate-spin" />}
        {(status || 'pending').replace('_', ' ')}
      </span>
    );
  };

  const allExtracted = tenderStatus?.status === 'extracted' && bidderFiles.length > 0 && bidderFiles.every(f => f.status?.status === 'extracted');

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="mb-6">
        <button onClick={() => navigate('/dashboard')} className="text-sm font-medium text-slate-500 hover:text-slate-800 mb-2 flex items-center gap-1">
          ← Back to Dashboard
        </button>
        <div className="flex justify-between items-end">
          <h1 className="text-2xl font-bold text-slate-900">Upload Documents</h1>
          <span className="text-sm font-medium text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full">Step 1 of 5</span>
        </div>
        <p className="text-sm text-slate-500 mt-1">Upload the tender and all bidder submissions to begin.</p>
      </div>

      <div className="grid sm:grid-cols-2 gap-4 mb-8">
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Department ID</label>
          <input value={departmentId} onChange={e => setDepartmentId(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm" placeholder="e.g. DEPT-PWD-UP" />
        </div>
        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">Tender ID</label>
          <input value={tenderId} onChange={e => setTenderId(e.target.value)} className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 text-sm" placeholder="e.g. TENDER-2024-001" />
        </div>
      </div>

      {/* Tender drop zone */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-slate-800 mb-3">Tender Document</h2>
        <div
          onDragOver={e => { e.preventDefault(); setTenderDragActive(true); }}
          onDragLeave={() => setTenderDragActive(false)}
          onDrop={e => { e.preventDefault(); setTenderDragActive(false); const f = e.dataTransfer.files[0]; if (f && ALLOWED.includes(f.type)) setTenderFile(f); }}
          className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer ${tenderDragActive ? 'border-indigo-500 bg-indigo-50' : tenderFile ? 'border-emerald-400 bg-emerald-50' : 'border-slate-300 hover:border-slate-400'}`}
          onClick={() => document.getElementById('tender-input')?.click()}
        >
          <input id="tender-input" type="file" className="hidden" accept=".pdf,.docx,.png,.jpg,.jpeg,.tiff" onChange={e => { if (e.target.files?.[0]) setTenderFile(e.target.files[0]); }} />
          {tenderFile ? (
            <div className="flex items-center justify-center gap-3">
              <span className="text-emerald-600 font-medium">{tenderFile.name}</span>
              <span className="text-xs text-slate-400">({(tenderFile.size / 1024 / 1024).toFixed(1)} MB)</span>
              {tenderStatus && statusChip(tenderStatus.status)}
            </div>
          ) : (
            <p className="text-slate-400">Drop tender document here or click to browse</p>
          )}
        </div>
      </div>

      {/* Bidder drop zone */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-slate-800 mb-3">Bidder Submissions</h2>
        <div
          onDragOver={e => { e.preventDefault(); setBidderDragActive(true); }}
          onDragLeave={() => setBidderDragActive(false)}
          onDrop={e => {
            e.preventDefault(); setBidderDragActive(false);
            const files = Array.from(e.dataTransfer.files).filter(f => ALLOWED.includes(f.type));
            setBidderFiles(prev => [...prev, ...files.map(f => ({ file: f, bidderId: '', status: null }))]);
          }}
          className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer ${bidderDragActive ? 'border-indigo-500 bg-indigo-50' : bidderFiles.length > 0 ? 'border-emerald-400 bg-emerald-50' : 'border-slate-300 hover:border-slate-400'}`}
          onClick={() => document.getElementById('bidder-input')?.click()}
        >
          <input id="bidder-input" type="file" className="hidden" multiple accept=".pdf,.docx,.png,.jpg,.jpeg,.tiff" onChange={e => { if (e.target.files) setBidderFiles(prev => [...prev, ...Array.from(e.target.files!).map(f => ({ file: f, bidderId: '', status: null }))]); }} />
          <p className="text-slate-400">{bidderFiles.length > 0 ? `${bidderFiles.length} file(s) added` : 'Drop bidder documents here or click to browse'}</p>
        </div>

        {bidderFiles.length > 0 && (
          <div className="mt-4 space-y-3">
            {bidderFiles.map((entry, i) => (
              <div key={i} className="flex items-center gap-3 bg-white p-3 rounded-lg border border-slate-200">
                <span className="text-sm text-slate-700 flex-1 truncate">{entry.file.name}</span>
                <input value={entry.bidderId} onChange={e => { const n = [...bidderFiles]; n[i].bidderId = e.target.value; setBidderFiles(n); }}
                  className="w-40 px-2 py-1.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500" placeholder="Bidder ID" />
                {entry.status && statusChip(entry.status.status)}
                <button onClick={() => setBidderFiles(prev => prev.filter((_, j) => j !== i))} className="text-slate-400 hover:text-red-500 transition-colors">✕</button>
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="flex gap-4">
        <button onClick={handleUpload} disabled={!tenderFile || !departmentId || !tenderId || uploading}
          className="px-6 py-3 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-all disabled:opacity-50 disabled:cursor-not-allowed active:scale-95">
          {uploading ? 'Uploading...' : 'Upload & Process'}
        </button>
        {allExtracted && (
          <button onClick={() => navigate(`/criteria/${tenderId}`)} className="px-6 py-3 bg-emerald-600 text-white font-semibold rounded-xl hover:bg-emerald-700 transition-all active:scale-95">
            Proceed to Criteria Review →
          </button>
        )}
      </div>
    </div>
  );
};

export default Upload;
