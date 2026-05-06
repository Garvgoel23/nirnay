import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: string;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, requiredRole }) => {
  const { user, role, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/" replace />;
  }

  if (requiredRole && role !== requiredRole) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <h2 className="text-2xl font-semibold text-slate-700">Unauthorized</h2>
        <p className="text-slate-500">You do not have permission to access this page.</p>
        <a href="/dashboard" className="text-indigo-600 hover:text-indigo-700 font-medium">Go to Dashboard</a>
      </div>
    );
  }

  return <>{children}</>;
};

export default ProtectedRoute;
