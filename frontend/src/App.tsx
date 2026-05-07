import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Footer from './components/Footer';
import ProtectedRoute from './components/ProtectedRoute';
import Home from './pages/Home';
import About from './pages/About';
import Dashboard from './pages/Dashboard';
import Tenders from './pages/Tenders';
import Upload from './pages/Upload';
import Criteria from './pages/Criteria';
import Results from './pages/Results';
import Compare from './pages/Compare';
import Anomalies from './pages/Anomalies';
import Review from './pages/Review';
import Export from './pages/Export';
import Privacy from './pages/Privacy';
import Terms from './pages/Terms';
import NotFound from './pages/NotFound';

const App: React.FC = () => {
  return (
    <>
      <Navbar />
      <main className="flex-1">
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<Home />} />
          <Route path="/about" element={<About />} />
          <Route path="/privacy" element={<Privacy />} />
          <Route path="/terms" element={<Terms />} />
          {/* Auth-guarded routes */}
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/tenders" element={<ProtectedRoute><Tenders /></ProtectedRoute>} />
          <Route path="/upload" element={<ProtectedRoute><Upload /></ProtectedRoute>} />
          <Route path="/criteria/:tenderId" element={<ProtectedRoute><Criteria /></ProtectedRoute>} />
          <Route path="/results/:tenderId" element={<ProtectedRoute><Results /></ProtectedRoute>} />
          <Route path="/compare/:tenderId" element={<ProtectedRoute><Compare /></ProtectedRoute>} />
          <Route path="/anomalies/:tenderId" element={<ProtectedRoute><Anomalies /></ProtectedRoute>} />
          <Route path="/review/:tenderId" element={<ProtectedRoute><Review /></ProtectedRoute>} />
          <Route path="/export/:tenderId" element={<ProtectedRoute><Export /></ProtectedRoute>} />
          {/* Catch-all */}
          <Route path="*" element={<NotFound />} />
        </Routes>
      </main>
      <Footer />
    </>
  );
};

export default App;
