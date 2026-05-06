import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import client from '../api/client';
import { DashboardSummary } from '../types';

const Dashboard: React.FC = () => {
  const { user, role } = useAuth();
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [loading, setLoading] = useState(true);

  const getGreeting = () => {
    const h = new Date().getHours();
    if (h >= 5 && h < 12) return 'Good morning';
    if (h >= 12 && h < 17) return 'Good afternoon';
    if (h >= 17 && h < 24) return 'Good evening';
    return 'Good night';
  };

  useEffect(() => {
    client.get('/api/dashboard/summary').then(r => setSummary(r.data)).catch(console.error).finally(() => setLoading(false));
  }, []);

  const completedThisMonth = summary?.recent_activity?.filter(a => {
    if (a.action_type !== 'sign_off' || !a.timestamp) return false;
    const d = new Date(a.timestamp);
    const now = new Date();
    return d.getMonth() === now.getMonth() && d.getFullYear() === now.getFullYear();
  }).length || 0;

  if (loading) return <div className="flex items-center justify-center min-h-[60vh]"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" /></div>;

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Greeting */}
      <div className="flex items-center gap-3 mb-8">
        <h1 className="text-2xl font-semibold text-slate-800">{getGreeting()}, {user?.displayName || 'Officer'}</h1>
        <span className={`px-3 py-1 text-xs font-medium rounded-full ${role === 'senior_officer' ? 'bg-emerald-100 text-emerald-700' : 'bg-indigo-100 text-indigo-700'}`}>
          {role === 'senior_officer' ? 'Senior Officer' : 'Officer'}
        </span>
      </div>

      {/* Stats */}
      <div className="grid sm:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-2xl border border-slate-200 p-6 hover:shadow-lg transition-shadow">
          <p className="text-4xl font-bold text-indigo-700">{summary?.active_tenders || 0}</p>
          <p className="text-sm text-slate-500 mt-1">Active Tenders</p>
          <Link to="/tenders" className="text-xs text-indigo-600 hover:text-indigo-700 mt-3 inline-block font-medium">View all →</Link>
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 p-6 hover:shadow-lg transition-shadow">
          <p className={`text-4xl font-bold ${(summary?.pending_review_count || 0) > 0 ? 'text-amber-600' : 'text-slate-400'}`}>{summary?.pending_review_count || 0}</p>
          <p className="text-sm text-slate-500 mt-1">Pending Manual Reviews</p>
          {(summary?.pending_review_count || 0) > 0 && <Link to="/tenders" className="text-xs text-amber-600 hover:text-amber-700 mt-3 inline-block font-medium">Go to Review Queue →</Link>}
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 p-6 hover:shadow-lg transition-shadow">
          <p className="text-4xl font-bold text-slate-700">{completedThisMonth}</p>
          <p className="text-sm text-slate-500 mt-1">Completed This Month</p>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 mb-8">
        <h2 className="text-lg font-semibold text-slate-800 mb-4">Recent Activity</h2>
        {(!summary?.recent_activity || summary.recent_activity.length === 0) ? (
          <p className="text-slate-400 text-sm py-4">No recent activity. Start by uploading a tender.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="border-b border-slate-100">
                <th className="text-left py-2 text-xs font-medium text-slate-400 uppercase">Tender ID</th>
                <th className="text-left py-2 text-xs font-medium text-slate-400 uppercase">Action</th>
                <th className="text-left py-2 text-xs font-medium text-slate-400 uppercase">Timestamp</th>
              </tr></thead>
              <tbody>
                {summary.recent_activity.map(a => (
                  <tr key={a.id} className="border-b border-slate-50 hover:bg-slate-50">
                    <td className="py-3 text-slate-700 font-mono text-xs">{a.target_id}</td>
                    <td className="py-3"><span className="px-2 py-0.5 text-xs font-medium bg-slate-100 text-slate-600 rounded-full">{a.action_type}</span></td>
                    <td className="py-3 text-slate-500 text-xs">{a.timestamp ? new Intl.DateTimeFormat('en-IN', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' }).format(new Date(a.timestamp)) : '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Quick Start */}
      <div className="bg-indigo-50 rounded-2xl p-6 border border-indigo-100">
        <h3 className="text-lg font-semibold text-slate-800">Start a new evaluation</h3>
        <p className="text-sm text-slate-600 mt-1">Upload the tender document and all bidder submissions. Processing starts automatically — you will be notified when evaluation is ready for review.</p>
        <Link to="/upload" className="mt-4 inline-block px-5 py-2.5 bg-indigo-600 text-white font-medium rounded-xl hover:bg-indigo-700 transition-all hover:shadow-lg hover:shadow-indigo-200 active:scale-95">Start New Evaluation</Link>
      </div>
    </div>
  );
};

export default Dashboard;
