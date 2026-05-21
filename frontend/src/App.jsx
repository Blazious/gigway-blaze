import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, Outlet } from 'react-router-dom';
import LandingPage from './pages/LandingPage';
import RegisterPage from './pages/RegisterPage';
import LoginPage from './pages/LoginPage';
import GoogleCallback from './pages/GoogleCallback';
import DashboardLayout from './layouts/DashboardLayout';
import FreelancerDashboard from './pages/dashboard/FreelancerDashboard';
import MyProjects from './pages/dashboard/MyProjects';
import FindWork from './pages/dashboard/FindWork';
import Wallet from './pages/dashboard/Wallet';
import ProjectDetails from './pages/dashboard/ProjectDetails';
import ClientDashboard from './pages/dashboard/ClientDashboard';
import CreateProject from './pages/dashboard/CreateProject';
import Disputes from './pages/dashboard/Disputes';
import Settings from './pages/dashboard/Settings';
import Notifications from './pages/dashboard/Notifications';
import LexaChatbot from './components/LexaChatbot';

// Simple Protected Route Wrapper
const ProtectedRoute = () => {
  const token = localStorage.getItem('token');
  return token ? <Outlet /> : <Navigate to="/login" replace />;
};

// Wrapper to decide which dashboard to show
const DashboardHome = () => {
  const user = JSON.parse(localStorage.getItem('user') || '{}');
  return user.user_type === 'client' ? <ClientDashboard /> : <FreelancerDashboard />;
};

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/auth/google/callback" element={<GoogleCallback />} />

        {/* Protected Dashboard Routes */}
        <Route element={<ProtectedRoute />}>
          <Route path="/dashboard" element={<DashboardLayout />}>
            <Route index element={<DashboardHome />} />
            {/* Future routes: projects, wallet, etc. */}
            <Route path="projects" element={<MyProjects />} />
            <Route path="projects/:id" element={<ProjectDetails />} />
            <Route path="find-work" element={<FindWork />} />
            <Route path="post-project" element={<CreateProject />} />
            <Route path="wallet" element={<Wallet />} />
            <Route path="disputes" element={<Disputes />} />
            <Route path="settings" element={<Settings />} />
            <Route path="notifications" element={<Notifications />} />
          </Route>
        </Route>
      </Routes>
      <LexaChatbot />
    </Router>
  );
}

export default App;
