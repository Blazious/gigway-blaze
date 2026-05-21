import React from 'react';
import { Outlet, NavLink, useNavigate } from 'react-router-dom';
import {
    LayoutDashboard,
    Briefcase,
    Wallet,
    MessageSquare,
    Settings,
    LogOut,
    Search,
    PlusCircle
} from 'lucide-react';
import '../styles/Dashboard.css';
import NotificationDropdown from '../components/NotificationDropdown';
import ProfileModal from '../components/ProfileModal';
import ThemeToggle from '../components/ThemeToggle';
import NetworkBackground from '../components/NetworkBackground';

const DashboardLayout = () => {
    const navigate = useNavigate();
    const [user, setUser] = React.useState(JSON.parse(localStorage.getItem('user') || '{}'));
    const [isProfileModalOpen, setIsProfileModalOpen] = React.useState(false);

    const handleLogout = () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        navigate('/login');
    };

    const handleProfileUpdate = (updatedUser) => {
        setUser(updatedUser);
    };

    return (
        <div className="dashboard-container">
            <NetworkBackground />
            {/* Sidebar */}
            <aside className="sidebar">
                <div className="sidebar-header">
                    <div className="sidebar-logo">EscrowGig</div>
                </div>

                <nav className="sidebar-nav" id="tour-sidebar">
                    <NavLink to="/dashboard" end className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} id="tour-home">
                        <LayoutDashboard /> Dashboard
                    </NavLink>

                    {/* Freelancer Links */}
                    {user.user_type === 'freelancer' && (
                        <NavLink to="/dashboard/find-work" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} id="tour-find-work">
                            <Search /> Find Work
                        </NavLink>
                    )}

                    {/* Client Links */}
                    {user.user_type === 'client' && (
                        <NavLink to="/dashboard/post-project" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`} id="tour-post-project">
                            <PlusCircle /> Post Project
                        </NavLink>
                    )}

                    <NavLink to="/dashboard/projects" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                        <Briefcase /> My Projects
                    </NavLink>
                    <NavLink to="/dashboard/wallet" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                        <Wallet /> Wallet
                    </NavLink>
                    <NavLink to="/dashboard/disputes" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                        <MessageSquare /> Disputes
                    </NavLink>
                    <NavLink to="/dashboard/settings" className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
                        <Settings /> Settings
                    </NavLink>
                </nav>

                <div className="sidebar-footer">
                    <button onClick={handleLogout} className="logout-btn">
                        <LogOut size={20} /> Logout
                    </button>
                </div>
            </aside>

            {/* Main Content */}
            <main className="main-content">
                <header className="dashboard-header">
                    <h1 className="page-title">Dashboard</h1>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem' }}>
                        <ThemeToggle />
                        <div id="tour-notifications">
                            <NotificationDropdown />
                        </div>
                        <div className="user-profile" onClick={() => setIsProfileModalOpen(true)} style={{ cursor: 'pointer' }}>
                            <span>Welcome, {user.email?.split('@')[0] || 'User'}</span>
                            <div className="user-avatar">
                                {user.profile_picture ? (
                                    <img src={user.profile_picture} alt="Profile" style={{ width: '100%', height: '100%', objectFit: 'cover', borderRadius: '50%' }} />
                                ) : (
                                    user.email?.[0].toUpperCase() || 'U'
                                )}
                            </div>
                        </div>
                    </div>
                </header>

                {/* Page Content Rendered Here */}
                <Outlet />

                <ProfileModal
                    isOpen={isProfileModalOpen}
                    onClose={() => setIsProfileModalOpen(false)}
                    user={user}
                    onUpdate={handleProfileUpdate}
                />
            </main>
        </div>
    );
};

export default DashboardLayout;
