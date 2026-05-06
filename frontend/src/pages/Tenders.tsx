import React, { useEffect, useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import client from '../api/client';

interface TenderSummary {
  tender_id: string;
  department_id: string;
  status: string;
  bidder_count: number;
  anomaly_count: number;
  critical_anomalies: number;
  created_at: string;
}

const Tenders: React.FC = () => {
  const navigate = useNavigate();
  const [tenders, setTenders] = useState<TenderSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    client.get('/api/dashboard/tenders')
      .then(r => setTenders(r.data.tenders || []))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      uploaded: 'bg-slate-100 text-slate-600',
      ocr_processing: 'bg-blue-100 text-blue-700',
      ocr_complete: 'bg-blue-50 text-blue-600',
      extracting: 'bg-indigo-100 text-indigo-700',
      ready_for_evaluation: 'bg-emerald-100 text-emerald-700',
      evaluated: 'bg-purple-100 text-purple-700',
      error: 'bg-red-100 text-red-700',
    };
    return (
      <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${styles[status] || 'bg-slate-100 text-slate-600'}`}>
        {status.replace(/_/g, ' ')}
      </span>
    );
  };

  if (loading) return <div className="flex items-center justify-center min-h-[60vh]"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" /></div>;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex justify-between items-center mb-8">
        <div>
          <button onClick={() => navigate('/dashboard')} className="text-sm font-medium text-slate-500 hover:text-slate-800 mb-2 flex items-center gap-1">
            ← Back to Dashboard
          </button>
          <h1 className="text-2xl font-bold text-slate-900">All Tenders</h1>
          <p className="text-sm text-slate-500 mt-1">Overview of all proposals and their processing status.</p>
        </div>
        <Link to="/upload" className="px-5 py-2.5 bg-indigo-600 text-white font-medium rounded-xl hover:bg-indigo-700 transition-all hover:shadow-lg hover:shadow-indigo-200 active:scale-95">
          + New Tender
        </Link>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden shadow-sm">
        <table className="w-full text-sm text-left">
          <thead className="bg-slate-50 border-b border-slate-200">
            <tr>
              <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Tender ID</th>
              <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Department</th>
              <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Bidders</th>
              <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Violations / Anomalies</th>
              <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {tenders.length === 0 ? (
              <tr><td colSpan={6} className="px-6 py-8 text-center text-slate-500">No tenders found.</td></tr>
            ) : (
              tenders.map((tender) => (
                <tr key={tender.tender_id} className="hover:bg-slate-50 transition-colors">
                  <td className="px-6 py-4 font-mono font-medium text-slate-800">{tender.tender_id}</td>
                  <td className="px-6 py-4 text-slate-600">{tender.department_id}</td>
                  <td className="px-6 py-4">{getStatusBadge(tender.status)}</td>
                  <td className="px-6 py-4 text-slate-600">{tender.bidder_count}</td>
                  <td className="px-6 py-4">
                    {tender.anomaly_count > 0 ? (
                      <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${tender.critical_anomalies > 0 ? 'bg-red-100 text-red-700' : 'bg-amber-100 text-amber-700'}`}>
                        {tender.anomaly_count} detected ({tender.critical_anomalies} critical)
                      </span>
                    ) : (
                      <span className="text-slate-400 text-xs">—</span>
                    )}
                  </td>
                  <td className="px-6 py-4 text-right space-x-3">
                    <Link to={`/criteria/${tender.tender_id}`} className="text-indigo-600 hover:text-indigo-800 font-medium text-xs">Criteria</Link>
                    {tender.status === 'evaluated' && (
                      <Link to={`/results/${tender.tender_id}`} className="text-indigo-600 hover:text-indigo-800 font-medium text-xs">Results</Link>
                    )}
                    {tender.anomaly_count > 0 && (
                      <Link to={`/anomalies/${tender.tender_id}`} className="text-amber-600 hover:text-amber-800 font-medium text-xs">View Anomalies</Link>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Tenders;
