import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const Navbar: React.FC = () => {
  const { user, role, signInWithGoogle, logout } = useAuth();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [profileOpen, setProfileOpen] = useState(false);

  const isActive = (path: string) => location.pathname === path;

  const getInitials = (name: string | null) => {
    if (!name) return '?';
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  return (
    <nav className="bg-white/80 backdrop-blur-lg border-b border-slate-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Left: Logo */}
          <div className="flex items-center gap-3">
            <Link to={user ? '/dashboard' : '/'} className="flex items-center gap-2 group">
              {/* Ashoka Chakra-inspired SVG */}
              <svg width="32" height="32" viewBox="0 0 32 32" className="text-indigo-600 group-hover:rotate-[30deg] transition-transform duration-500">
                <circle cx="16" cy="16" r="14" fill="none" stroke="currentColor" strokeWidth="2"/>
                <circle cx="16" cy="16" r="4" fill="currentColor"/>
                {[...Array(12)].map((_, i) => (
                  <line key={i} x1="16" y1="6" x2="16" y2="10" stroke="currentColor" strokeWidth="1.5"
                    transform={`rotate(${i * 30} 16 16)`} strokeLinecap="round"/>
                ))}
              </svg>
              <span className="text-xl font-bold bg-gradient-to-r from-indigo-700 to-indigo-500 bg-clip-text text-transparent">
                Nirṇay
              </span>
            </Link>
          </div>

          {/* Right: Desktop nav */}
          <div className="hidden md:flex items-center gap-1">
            {!user ? (
              <>
                <Link to="/" className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${isActive('/') ? 'text-indigo-700 bg-indigo-50' : 'text-slate-600 hover:text-indigo-600 hover:bg-slate-50'}`}>Home</Link>
                <Link to="/about" className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${isActive('/about') ? 'text-indigo-700 bg-indigo-50' : 'text-slate-600 hover:text-indigo-600 hover:bg-slate-50'}`}>About</Link>
                <button onClick={signInWithGoogle} className="ml-3 px-4 py-2 bg-indigo-600 text-white text-sm font-medium rounded-lg hover:bg-indigo-700 transition-all hover:shadow-lg hover:shadow-indigo-200 active:scale-95">
                  Sign In with Google
                </button>
              </>
            ) : (
              <>
                <Link to="/dashboard" className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${isActive('/dashboard') ? 'text-indigo-700 bg-indigo-50' : 'text-slate-600 hover:text-indigo-600 hover:bg-slate-50'}`}>Dashboard</Link>
                <div className="relative ml-3">
                  <button onClick={() => setProfileOpen(!profileOpen)} className="w-9 h-9 rounded-full bg-gradient-to-br from-indigo-500 to-indigo-700 text-white text-sm font-semibold flex items-center justify-center hover:shadow-lg hover:shadow-indigo-200 transition-all">
                    {getInitials(user.displayName)}
                  </button>
                  {profileOpen && (
                    <div className="absolute right-0 mt-2 w-64 bg-white rounded-xl shadow-xl border border-slate-100 py-2 animate-fade-in">
                      <div className="px-4 py-3 border-b border-slate-100">
                        <p className="text-sm font-semibold text-slate-800">{user.displayName}</p>
                        <p className="text-xs text-slate-500 mt-0.5">{user.email}</p>
                        <span className={`inline-block mt-2 px-2 py-0.5 text-xs font-medium rounded-full ${role === 'senior_officer' ? 'bg-emerald-100 text-emerald-700' : 'bg-indigo-100 text-indigo-700'}`}>
                          {role === 'senior_officer' ? 'Senior Officer' : 'Officer'}
                        </span>
                      </div>
                      <button onClick={() => { logout(); setProfileOpen(false); }} className="w-full text-left px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 transition-colors">
                        Sign Out
                      </button>
                    </div>
                  )}
                </div>
              </>
            )}
          </div>

          {/* Mobile hamburger */}
          <button onClick={() => setMobileOpen(!mobileOpen)} className="md:hidden p-2 rounded-lg text-slate-500 hover:bg-slate-100">
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              {mobileOpen ? <path d="M6 18L18 6M6 6l12 12"/> : <path d="M3 12h18M3 6h18M3 18h18"/>}
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile drawer */}
      {mobileOpen && (
        <div className="md:hidden border-t border-slate-100 bg-white animate-fade-in">
          <div className="px-4 py-3 space-y-1">
            {!user ? (
              <>
                <Link to="/" onClick={() => setMobileOpen(false)} className={`block px-3 py-2.5 rounded-lg text-sm font-medium ${isActive('/') ? 'text-indigo-700 bg-indigo-50 border-l-4 border-indigo-600' : 'text-slate-600'}`}>Home</Link>
                <Link to="/about" onClick={() => setMobileOpen(false)} className={`block px-3 py-2.5 rounded-lg text-sm font-medium ${isActive('/about') ? 'text-indigo-700 bg-indigo-50 border-l-4 border-indigo-600' : 'text-slate-600'}`}>About</Link>
                <button onClick={() => { signInWithGoogle(); setMobileOpen(false); }} className="w-full mt-2 px-4 py-2.5 bg-indigo-600 text-white text-sm font-medium rounded-lg">Sign In with Google</button>
              </>
            ) : (
              <>
                <Link to="/dashboard" onClick={() => setMobileOpen(false)} className={`block px-3 py-2.5 rounded-lg text-sm font-medium ${isActive('/dashboard') ? 'text-indigo-700 bg-indigo-50 border-l-4 border-indigo-600' : 'text-slate-600'}`}>Dashboard</Link>
                <div className="pt-3 mt-3 border-t border-slate-100">
                  <p className="px-3 text-sm font-semibold text-slate-800">{user.displayName}</p>
                  <p className="px-3 text-xs text-slate-500">{user.email}</p>
                  <button onClick={() => { logout(); setMobileOpen(false); }} className="mt-2 w-full px-3 py-2.5 text-sm text-red-600 text-left rounded-lg hover:bg-red-50">Sign Out</button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </nav>
  );
};

export default Navbar;
