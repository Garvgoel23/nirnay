import React from 'react';
import { useAuth } from '../context/AuthContext';

const Home: React.FC = () => {
  const { signInWithGoogle } = useAuth();

  return (
    <div>
      {/* Hero */}
      <section className="relative overflow-hidden bg-gradient-to-br from-slate-50 via-white to-indigo-50">
        <div className="absolute inset-0 opacity-30" style={{ backgroundImage: 'repeating-linear-gradient(135deg, transparent, transparent 40px, rgba(99,102,241,0.03) 40px, rgba(99,102,241,0.03) 80px)' }} />
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 lg:py-28 relative">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div className="animate-fade-in-up">
              <h1 className="text-5xl lg:text-6xl font-extrabold text-slate-900 leading-tight">Nirṇay</h1>
              <p className="mt-4 text-xl text-slate-600 leading-relaxed">Transparent, traceable, AI-assisted bid evaluation for Indian government procurement.</p>
              <div className="mt-8 flex flex-wrap gap-4">
                <button onClick={signInWithGoogle} className="px-6 py-3 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 transition-all hover:shadow-xl hover:shadow-indigo-200 active:scale-95">Sign In to Evaluate</button>
                <a href="#how-it-works" className="px-6 py-3 border-2 border-indigo-200 text-indigo-700 font-semibold rounded-xl hover:bg-indigo-50 transition-all">Learn How It Works</a>
              </div>
            </div>
            <div className="hidden lg:flex justify-center">
              {/* Abstract doc illustration */}
              <div className="relative w-80 h-64">
                {[{ x: 0, y: 0, color: '#22c55e', icon: '✓' }, { x: 40, y: 20, color: '#ef4444', icon: '✗' }, { x: 80, y: 40, color: '#f59e0b', icon: '?' }].map((doc, i) => (
                  <div key={i} className="absolute w-48 h-56 border-2 rounded-xl bg-white/80 backdrop-blur-sm flex items-center justify-center transition-transform hover:-translate-y-2 shadow-lg" style={{ left: doc.x, top: doc.y, borderColor: doc.color + '40', zIndex: 3 - i }}>
                    <span className="text-5xl" style={{ color: doc.color }}>{doc.icon}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Problem */}
      <section className="bg-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center text-slate-900 mb-12">The problem with manual procurement evaluation</h2>
          <div className="grid md:grid-cols-3 gap-8">
            {[
              { icon: '📄', title: 'Manual Evaluation is Slow', desc: 'Large tender volumes create multi-week backlogs and inconsistent assessments when different officers apply different interpretations of the same criterion.' },
              { icon: '🔗', title: 'Traceability Gaps', desc: 'When decisions are recorded only in spreadsheets, it is impossible to audit why a specific bidder was rejected or which document page was the basis for the verdict.' },
              { icon: '⚠️', title: 'Collusion is Hard to Detect', desc: 'Cross-bidder patterns like shared GST numbers, recycled experience certificates, or suspiciously clustered bid prices are invisible to any manual process.' },
            ].map((card, i) => (
              <div key={i} className="p-6 rounded-2xl border border-slate-200 hover:border-indigo-200 hover:shadow-lg transition-all group">
                <span className="text-3xl">{card.icon}</span>
                <h3 className="mt-4 text-lg font-bold text-slate-800 group-hover:text-indigo-700 transition-colors">{card.title}</h3>
                <p className="mt-2 text-sm text-slate-600 leading-relaxed">{card.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* How It Works */}
      <section id="how-it-works" className="bg-slate-50 py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center text-slate-900 mb-12">How Nirṇay works</h2>
          <div className="flex flex-col lg:flex-row items-start lg:items-center gap-4 lg:gap-0">
            {[
              { step: 1, title: 'Upload Documents', desc: 'Officer uploads the tender document and all bidder submission files.' },
              { step: 2, title: 'AI Extraction', desc: 'Gemini extracts eligibility criteria and corresponding values from every page.' },
              { step: 3, title: 'Credibility Check', desc: 'Documents scored for authenticity, anomalies detected, criteria checked for contradictions.' },
              { step: 4, title: 'Verdict Engine', desc: 'Rule-based comparators and LLM arbitration produce per-criterion verdicts.' },
              { step: 5, title: 'Review & Export', desc: 'Officer reviews borderline cases, signs off, generates PDF reports.' },
            ].map((s, i) => (
              <React.Fragment key={s.step}>
                <div className="flex lg:flex-col items-center lg:items-center gap-4 lg:gap-3 flex-1">
                  <div className="w-12 h-12 rounded-full bg-indigo-600 text-white flex items-center justify-center text-lg font-bold shrink-0 shadow-lg shadow-indigo-200">{s.step}</div>
                  <div className="lg:text-center">
                    <h3 className="font-semibold text-slate-800 text-sm">{s.title}</h3>
                    <p className="text-xs text-slate-500 mt-1 max-w-[180px]">{s.desc}</p>
                  </div>
                </div>
                {i < 4 && <div className="hidden lg:block w-12 h-0.5 bg-indigo-200 mt-6 shrink-0" />}
              </React.Fragment>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="bg-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-center text-slate-900 mb-12">What Nirṇay does</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {[
              { icon: '🔍', title: 'Multilingual OCR', desc: 'Supports native PDFs, scanned documents via Tesseract OCR, and Word files, with Hindi and English handled in the same pipeline.' },
              { icon: '📋', title: 'Criterion Extraction', desc: 'Gemini extracts every eligibility criterion including those in annexures, footnotes, and numbered conditions, with mandatory classification.' },
              { icon: '🕵️', title: 'Anomaly Detection', desc: 'Shared GST/PAN detection via entity graphs, recycled document flagging via TF-IDF, and price clustering via DBSCAN.' },
              { icon: '✅', title: 'Traceable Verdicts', desc: 'Every verdict stores the exact source page, text snippet, extracted value, threshold, confidence score, and full LLM reasoning chain.' },
              { icon: '👤', title: 'Officer Override', desc: 'Senior officers can override borderline verdicts with mandatory 20-character justification, logged as an immutable audit record.' },
              { icon: '📊', title: 'Audit-Ready Exports', desc: 'SHA-256-hashed PDF reports and audit logs generated in one click — the integrity hash verifies the report has not been altered.' },
            ].map((f, i) => (
              <div key={i} className="p-6 rounded-2xl border border-slate-100 bg-gradient-to-br from-white to-slate-50 hover:shadow-lg hover:border-indigo-100 transition-all group">
                <div className="w-12 h-12 rounded-xl bg-indigo-50 flex items-center justify-center text-2xl group-hover:bg-indigo-100 transition-colors">{f.icon}</div>
                <h3 className="mt-4 font-bold text-slate-800">{f.title}</h3>
                <p className="mt-2 text-sm text-slate-600 leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Compliance banner */}
      <section className="bg-amber-50 border-y border-amber-200 py-8">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <p className="text-sm text-amber-900 leading-relaxed">Nirṇay is designed in alignment with GFR 2017, CVC guidelines, and the principle that every procurement decision must be explainable, reproducible, and auditable. All LLM outputs are logged with SHA-256 prompt and response hashes. No verdict is final without officer sign-off.</p>
        </div>
      </section>

      {/* Final CTA */}
      <section className="bg-gradient-to-br from-indigo-700 to-indigo-900 py-20">
        <div className="max-w-3xl mx-auto px-4 text-center">
          <h2 className="text-3xl font-bold text-white mb-6">Ready to evaluate your next tender?</h2>
          <button onClick={signInWithGoogle} className="px-8 py-3.5 bg-white text-indigo-700 font-bold rounded-xl hover:shadow-2xl hover:shadow-indigo-900/30 transition-all active:scale-95 text-lg">Sign In with Google</button>
          <p className="mt-4 text-sm text-indigo-200">Access is restricted to authorised government officers. Contact your department administrator to be onboarded.</p>
        </div>
      </section>
    </div>
  );
};

export default Home;
