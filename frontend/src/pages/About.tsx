import React from 'react';

const About: React.FC = () => {
  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
      <h1 className="text-4xl font-bold text-slate-900">About Nirṇay</h1>
      <p className="mt-2 text-xl text-slate-500">Built for procurement officers, not for procurement vendors.</p>

      {/* Mission */}
      <section className="mt-12 grid lg:grid-cols-3 gap-12">
        <div className="lg:col-span-2 space-y-4 text-slate-700 leading-relaxed">
          <p>Indian government procurement involves thousands of tenders annually across hundreds of departments. Each tender requires manual verification of eligibility criteria across multiple bidder documents — a process that is time-consuming, difficult to standardise, and nearly impossible to audit at scale.</p>
          <p>Nirṇay automates the mechanical parts of this process. OCR extracts text from every page. Gemini reads the tender and identifies every eligibility criterion. For each criterion it searches every bidder document for the corresponding value. Rule-based comparators and LLM arbitration then produce a verdict with a full evidence trail.</p>
          <p>Officers remain in the loop for every borderline or ambiguous case. The system surfaces these in a dedicated review queue with all relevant evidence pre-loaded. Senior officers sign off on the complete evaluation before any communication is sent to bidders.</p>
          <p>The platform is designed around auditability. Every AI call is logged with its prompt hash, response hash, model name, token count, and latency. Every verdict is insert-only — once written, it cannot be altered, only superseded by a new verdict with a reference to the original. Every export includes a SHA-256 integrity hash of the underlying data.</p>
        </div>
        <div className="bg-gradient-to-br from-indigo-50 to-white rounded-2xl border border-indigo-100 p-6 flex flex-col justify-center gap-6">
          {[{ val: '12+', label: 'criteria types handled' }, { val: '3', label: 'document formats supported' }, { val: '100%', label: 'of verdicts traceable to source page' }].map((s, i) => (
            <div key={i} className="text-center">
              <div className="text-3xl font-extrabold text-indigo-700">{s.val}</div>
              <div className="text-sm text-slate-500 mt-1">{s.label}</div>
            </div>
          ))}
        </div>
      </section>

      {/* Technology */}
      <section className="mt-16 bg-slate-50 rounded-2xl p-8 border border-slate-200">
        <h2 className="text-2xl font-bold text-slate-900 mb-4">Technology</h2>
        <p className="text-slate-700 leading-relaxed">Nirṇay is built on FastAPI for the backend API, React and Vite for the frontend, PostgreSQL for the database with SQLAlchemy ORM and Alembic migrations, Google Gemini 2.0 Flash and 2.5 Pro for language model inference, Tesseract OCR for scanned document processing, Firebase for authentication and role management, and reportlab for PDF generation. The entire platform deploys as three Docker containers — backend, frontend (served via Nginx), and PostgreSQL — with a single <code className="px-1.5 py-0.5 bg-slate-200 rounded text-sm font-mono">docker compose up --build</code> command.</p>
      </section>

      {/* Design principles */}
      <section className="mt-16">
        <h2 className="text-2xl font-bold text-slate-900 mb-6">Design principles</h2>
        <div className="grid sm:grid-cols-2 gap-6">
          {[
            { title: 'Audit-first', desc: 'Every write from an AI decision is insert-only. evaluation_verdicts, llm_audit_log, and officer_actions are append-only by design.' },
            { title: 'Officer-in-the-loop', desc: 'The system produces verdicts but cannot finalise an evaluation. Only a senior_officer can sign off, and that action is permanently logged.' },
            { title: 'Source-pinned', desc: 'Every extracted value stores the page number and exact text snippet. Every verdict links to that source for verification.' },
            { title: 'Transparent uncertainty', desc: 'Confidence scores and ambiguity reasons are first-class schema fields surfaced throughout the UI, not hidden footnotes.' },
          ].map((p, i) => (
            <div key={i} className="p-6 rounded-xl border border-slate-200 hover:border-indigo-200 transition-colors">
              <h3 className="font-bold text-slate-800">{p.title}</h3>
              <p className="mt-2 text-sm text-slate-600 leading-relaxed">{p.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Disclaimer */}
      <section className="mt-16 bg-amber-50 border border-amber-200 rounded-xl p-6">
        <h3 className="text-lg font-semibold text-amber-900">Disclaimer</h3>
        <p className="mt-2 text-sm text-amber-800 leading-relaxed">Nirṇay is a decision-support tool. It does not replace the judgement of the competent procurement authority. All evaluations must be reviewed and signed off by an authorised officer. The platform does not store data beyond what is required for evaluation and export. Departments are responsible for compliance with applicable data classification and retention policies.</p>
      </section>
    </div>
  );
};

export default About;
