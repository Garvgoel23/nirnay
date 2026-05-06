import React from 'react';

const Privacy: React.FC = () => (
  <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
    <h1 className="text-3xl font-bold text-slate-900">Privacy Policy</h1>
    <p className="text-sm text-slate-400 mt-2">Last updated: May 2026</p>
    <div className="mt-8 space-y-8 text-slate-700 leading-relaxed">
      <section><h2 className="text-xl font-semibold text-slate-800 mb-3">1. Data Collected</h2><p>The platform collects government tender documents, bidder submission documents, officer email addresses and display names from Google SSO, and evaluation outputs. No personal data of bidders beyond what appears in their submitted documents is collected or stored separately.</p></section>
      <section><h2 className="text-xl font-semibold text-slate-800 mb-3">2. Data Use</h2><p>Data is used solely to perform bid evaluation for the department that uploaded it. It is not shared with any third party except the Google Gemini AI API which processes document text as part of the evaluation pipeline.</p></section>
      <section><h2 className="text-xl font-semibold text-slate-800 mb-3">3. Data Retention</h2><p>Documents and evaluation records are retained for the period required by the department's data retention policy. Officers can request deletion by contacting the grievance address.</p></section>
      <section><h2 className="text-xl font-semibold text-slate-800 mb-3">4. Security</h2><p>All data in transit is encrypted via TLS. Data at rest is stored in a PostgreSQL database on the department's own infrastructure. API keys and credentials are never logged or stored in evaluation records.</p></section>
    </div>
  </div>
);

export default Privacy;
