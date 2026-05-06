import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Footer: React.FC = () => {
  const { user, signInWithGoogle } = useAuth();
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-slate-900 text-slate-300 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Column 1: Brand */}
          <div>
            <h3 className="text-white font-semibold text-lg">Nirṇay</h3>
            <p className="mt-2 text-sm text-slate-400">AI-assisted procurement evaluation for Indian government departments.</p>
            <p className="mt-2 text-xs text-slate-500">Aligned with GFR 2017 and CVC guidelines.</p>
          </div>
          {/* Column 2: Navigate */}
          <div>
            <h4 className="text-white font-medium text-sm uppercase tracking-wider mb-3">Navigate</h4>
            <ul className="space-y-2">
              <li><Link to="/" className="text-sm text-slate-400 hover:text-indigo-400 transition-colors">Home</Link></li>
              <li><Link to="/about" className="text-sm text-slate-400 hover:text-indigo-400 transition-colors">About</Link></li>
              <li>
                {user ? (
                  <Link to="/dashboard" className="text-sm text-slate-400 hover:text-indigo-400 transition-colors">Dashboard</Link>
                ) : (
                  <button onClick={signInWithGoogle} className="text-sm text-slate-400 hover:text-indigo-400 transition-colors">Sign In</button>
                )}
              </li>
            </ul>
          </div>
          {/* Column 3: Legal */}
          <div>
            <h4 className="text-white font-medium text-sm uppercase tracking-wider mb-3">Legal & Support</h4>
            <ul className="space-y-2">
              <li><Link to="/privacy" className="text-sm text-slate-400 hover:text-indigo-400 transition-colors">Privacy Policy</Link></li>
              <li><Link to="/terms" className="text-sm text-slate-400 hover:text-indigo-400 transition-colors">Terms of Use</Link></li>
              <li><a href="mailto:grievance@nirnay.gov.in" className="text-sm text-slate-400 hover:text-indigo-400 transition-colors">Grievance</a></li>
            </ul>
          </div>
        </div>
      </div>
      <div className="border-t border-slate-800">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-col sm:flex-row justify-between items-center gap-2">
          <p className="text-xs text-slate-500">© {currentYear} Nirṇay. Built for transparent public procurement.</p>
          <p className="text-xs text-slate-500">Made in India 🇮🇳</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
