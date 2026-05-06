import React from 'react';

const Terms: React.FC = () => (
  <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
    <h1 className="text-3xl font-bold text-slate-900">Terms of Use</h1>
    <p className="text-sm text-slate-400 mt-2">Last updated: May 2026</p>
    <div className="mt-8 space-y-8 text-slate-700 leading-relaxed">
      <section><h2 className="text-xl font-semibold text-slate-800 mb-3">1. Authorised Use</h2><p>This platform is for use by authorised government procurement officers only. Unauthorised access is prohibited.</p></section>
      <section><h2 className="text-xl font-semibold text-slate-800 mb-3">2. No Warranty</h2><p>The platform is provided as a decision-support tool. The Government of India and the platform operators make no warranty that evaluation outputs are free of error. All outputs must be reviewed by a competent officer before use.</p></section>
      <section><h2 className="text-xl font-semibold text-slate-800 mb-3">3. Liability</h2><p>The platform operators are not liable for procurement decisions made on the basis of platform outputs. Officers and departments remain responsible for compliance with GFR 2017, CVC guidelines, and applicable procurement rules.</p></section>
    </div>
  </div>
);

export default Terms;
