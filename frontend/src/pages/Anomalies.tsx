import React, { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import client from '../api/client';
import { Anomaly } from '../types';
import AnomalyGraph from '../components/AnomalyGraph';

const severityBadge: Record<string, string> = { critical: 'bg-red-100 text-red-700', high: 'bg-orange-100 text-orange-700', medium: 'bg-amber-100 text-amber-700', low: 'bg-slate-100 text-slate-600' };

const Anomalies: React.FC = () => {
  const { tenderId } = useParams<{ tenderId: string }>();
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);

  useEffect(() => {
    if (!tenderId) return;
    client.get(`/api/credibility/anomalies/${tenderId}`).then(r => setAnomalies(r.data.anomalies || [])).catch(console.error).finally(() => setLoading(false));
  }, [tenderId]);

  if (loading) return <div className="flex items-center justify-center min-h-[60vh]"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" /></div>;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-slate-900 mb-2">Anomaly Detection</h1>
      <p className="text-sm text-slate-500 mb-8">Tender: {tenderId}</p>

      <div className="bg-white rounded-2xl border border-slate-200 p-6 mb-8">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Entity Relationship Graph</h2>
        <AnomalyGraph anomalies={anomalies} />
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead><tr className="bg-slate-50 border-b border-slate-200">
            <th className="text-left px-4 py-3 text-xs font-medium text-slate-400 uppercase">Type</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-slate-400 uppercase">Severity</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-slate-400 uppercase">Bidders Involved</th>
            <th className="text-left px-4 py-3 text-xs font-medium text-slate-400 uppercase">Details</th>
          </tr></thead>
          <tbody>
            {anomalies.map(a => (
              <React.Fragment key={a.id}>
                <tr className="border-b border-slate-50 hover:bg-slate-50 transition-colors">
                  <td className="px-4 py-3"><span className="px-2 py-0.5 text-xs font-medium bg-indigo-100 text-indigo-700 rounded-full">{a.anomaly_type.replace(/_/g, ' ')}</span></td>
                  <td className="px-4 py-3"><span className={`px-2 py-0.5 text-xs font-medium rounded-full ${severityBadge[a.severity] || ''}`}>{a.severity}</span></td>
                  <td className="px-4 py-3 text-slate-700">{a.bidder_ids.join(', ')}</td>
                  <td className="px-4 py-3"><button onClick={() => setExpanded(expanded === a.id ? null : a.id)} className="text-indigo-600 hover:text-indigo-700 text-xs font-medium">{expanded === a.id ? 'Collapse' : 'Expand'}</button></td>
                </tr>
                {expanded === a.id && (
                  <tr><td colSpan={4} className="px-4 py-3 bg-slate-50">
                    <pre className="text-xs font-mono text-slate-600 whitespace-pre-wrap">{JSON.stringify(a.evidence, null, 2)}</pre>
                  </td></tr>
                )}
              </React.Fragment>
            ))}
            {anomalies.length === 0 && <tr><td colSpan={4} className="px-4 py-8 text-center text-slate-400">No anomalies detected</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Anomalies;
