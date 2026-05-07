import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import client from '../api/client';
import { DashboardSummary } from '../types';

// ── Activity config — keys must match the action_type stored in DB ───────────
const activityConfig: Record<string, { label: string; icon: string; bg: string; text: string }> = {
  tender_uploaded:     { label: 'Tender Uploaded',         icon: '📄', bg: 'bg-indigo-50',  text: 'text-indigo-600'  },
  bid_uploaded:        { label: 'Bid Uploaded',             icon: '📂', bg: 'bg-blue-50',    text: 'text-blue-600'    },
  evaluation_complete: { label: 'Evaluation Complete',      icon: '🤖', bg: 'bg-emerald-50', text: 'text-emerald-600' },
  override_verdict:    { label: 'Officer Override',         icon: '✏️',  bg: 'bg-amber-50',  text: 'text-amber-700'   },
  override:            { label: 'Officer Override',         icon: '✏️',  bg: 'bg-amber-50',  text: 'text-amber-700'   },
  sign_off:            { label: 'Tender Signed Off',        icon: '✅', bg: 'bg-emerald-50', text: 'text-emerald-700' },
  reject:              { label: 'Bidder Rejected',          icon: '❌', bg: 'bg-red-50',     text: 'text-red-600'     },
  letter_drafted:      { label: 'Rejection Letter Drafted', icon: '📨', bg: 'bg-slate-50',   text: 'text-slate-600'   },
};

// Is this string a UUID? If so, don't show it as the primary label
const isUuid = (s: string) => /^[0-9a-f-]{36}$/i.test(s);

const fmtTime = (ts: string) => {
  // Backend stores timestamps as naive UTC strings (no timezone suffix).
  // Append 'Z' so JS Date() treats them as UTC before converting to IST.
  const utc = ts.includes('Z') || ts.includes('+') ? ts : ts.replace(' ', 'T') + 'Z';
  return new Intl.DateTimeFormat('en-IN', {
    timeZone: 'Asia/Kolkata',
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  }).format(new Date(utc));
};

// ── Component ────────────────────────────────────────────────────────────────
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
    client.get('/api/dashboard/summary')
      .then(r => setSummary(r.data))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600" />
    </div>
  );

  const activities = summary?.recent_activity || [];

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">

      {/* Greeting */}
      <div className="flex items-center gap-3 mb-8">
        <h1 className="text-2xl font-semibold text-slate-800">
          {getGreeting()}, {user?.displayName || 'Officer'}
        </h1>
        <span className={`px-3 py-1 text-xs font-medium rounded-full ${
          role === 'senior_officer' ? 'bg-emerald-100 text-emerald-700' : 'bg-indigo-100 text-indigo-700'
        }`}>
          {role === 'senior_officer' ? '⭐ Senior Officer' : 'Officer'}
        </span>
      </div>

      {/* Stats */}
      <div className="grid sm:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-2xl border border-slate-200 p-6 hover:shadow-lg transition-shadow">
          <p className="text-4xl font-bold text-indigo-700">{summary?.active_tenders || 0}</p>
          <p className="text-sm text-slate-500 mt-1">Active Tenders</p>
          <Link to="/tenders" className="text-xs text-indigo-600 hover:text-indigo-700 mt-3 inline-block font-medium">
            View all →
          </Link>
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 p-6 hover:shadow-lg transition-shadow">
          <p className={`text-4xl font-bold ${(summary?.pending_review_count || 0) > 0 ? 'text-amber-600' : 'text-slate-400'}`}>
            {summary?.pending_review_count || 0}
          </p>
          <p className="text-sm text-slate-500 mt-1">Pending Manual Reviews</p>
          {(summary?.pending_review_count || 0) > 0 && (
            <Link to="/tenders" className="text-xs text-amber-600 hover:text-amber-700 mt-3 inline-block font-medium">
              Go to Review Queue →
            </Link>
          )}
        </div>
        <div className="bg-white rounded-2xl border border-slate-200 p-6 hover:shadow-lg transition-shadow">
          <p className="text-4xl font-bold text-slate-700">{summary?.completed_this_month || 0}</p>
          <p className="text-sm text-slate-500 mt-1">Signed Off This Month</p>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 mb-8">
        <div className="flex items-center justify-between mb-5">
          <h2 className="text-lg font-semibold text-slate-800">Recent Activity</h2>
          <span className="text-xs text-slate-400">{activities.length} events</span>
        </div>

        {activities.length === 0 ? (
          <div className="flex flex-col items-center py-10 text-center">
            <div className="text-4xl mb-3">🚀</div>
            <p className="text-slate-600 font-medium">No activity yet</p>
            <p className="text-sm text-slate-400 mt-1">Upload a tender document to get started.</p>
          </div>
        ) : (
          <div className="space-y-1">
            {activities.map((a: any, i: number) => {
              const cfg = activityConfig[a.action_type] || {
                label: a.action_type?.replace(/_/g, ' '),
                icon: '🔹', bg: 'bg-slate-50', text: 'text-slate-600',
              };
              return (
                <div key={a.id ?? i} className={`flex items-start gap-3 p-3 rounded-xl ${cfg.bg} hover:opacity-90 transition-opacity`}>
                  {/* Icon */}
                  <span className="text-lg leading-none mt-0.5">{cfg.icon}</span>

                  {/* Body */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className={`text-xs font-semibold uppercase tracking-wide ${cfg.text}`}>
                        {cfg.label}
                      </span>
                      {/* Show filename / comment as primary detail */}
                      {a.detail && (
                        <span className="text-xs text-slate-600 font-medium truncate max-w-[280px]" title={a.detail}>
                          {a.detail}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 mt-0.5">
                      {/* Only show target_id if it's human-readable (not a UUID) */}
                      {a.target_id && !isUuid(a.target_id) && (
                        <span className="font-mono text-xs text-slate-400 truncate max-w-[200px]">
                          {a.target_id}
                        </span>
                      )}
                      {a.actor && a.actor !== 'system' && a.actor !== 'AI Engine' && (
                        <span className="text-xs text-slate-400">by {a.actor}</span>
                      )}
                      {a.actor === 'AI Engine' && (
                        <span className="text-xs text-indigo-400 font-medium">by AI Engine</span>
                      )}
                    </div>
                  </div>

                  {/* Timestamp */}
                  {a.timestamp && (
                    <span className="text-xs text-slate-400 shrink-0 mt-0.5">{fmtTime(a.timestamp)}</span>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Quick Start */}
      <div className="bg-indigo-50 rounded-2xl p-6 border border-indigo-100">
        <h3 className="text-lg font-semibold text-slate-800">Start a new evaluation</h3>
        <p className="text-sm text-slate-600 mt-1">
          Upload the tender document and all bidder submissions. Processing starts automatically —
          you will be notified when evaluation is ready for review.
        </p>
        <Link
          to="/upload"
          className="mt-4 inline-block px-5 py-2.5 bg-indigo-600 text-white font-medium rounded-xl hover:bg-indigo-700 transition-all hover:shadow-lg hover:shadow-indigo-200 active:scale-95"
        >
          Start New Evaluation
        </Link>
      </div>
    </div>
  );
};

export default Dashboard;
