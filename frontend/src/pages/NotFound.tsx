import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

const NotFound: React.FC = () => {
  const { user } = useAuth();
  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] px-4 text-center">
      <p className="text-8xl font-bold text-slate-200">404</p>
      <h2 className="mt-4 text-2xl font-semibold text-slate-700">Page not found</h2>
      <p className="mt-2 text-slate-500 max-w-md">The page you are looking for does not exist or you do not have permission to view it.</p>
      <div className="mt-8 flex gap-4">
        <Link to="/" className="px-5 py-2.5 border border-slate-300 text-slate-700 font-medium rounded-xl hover:bg-slate-50 transition-colors">Go Home</Link>
        {user && <Link to="/dashboard" className="px-5 py-2.5 bg-indigo-600 text-white font-medium rounded-xl hover:bg-indigo-700 transition-all">Go to Dashboard</Link>}
      </div>
    </div>
  );
};

export default NotFound;
