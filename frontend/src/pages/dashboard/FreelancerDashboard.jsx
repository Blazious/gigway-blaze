import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { DollarSign, Briefcase, Clock, CheckCircle, ShieldCheck, ArrowRight } from 'lucide-react';
import { getWallet, getProjects, getProfile } from '../../api';

const FreelancerDashboard = () => {
    const navigate = useNavigate();
    const [user, setUser] = useState(JSON.parse(localStorage.getItem('user') || '{}'));
    const readiness = user.freelancer_readiness;
    const [stats, setStats] = useState({
        in_escrow: 0,
        total_earnings: 0,
        active_projects: 0,
        completed_projects: 0
    });
    const [recentProjects, setRecentProjects] = useState([]);

    useEffect(() => {
        fetchDashboardData();
    }, []);

    const fetchDashboardData = async () => {
        try {
            const freshUser = await getProfile();
            localStorage.setItem('user', JSON.stringify(freshUser));
            setUser(freshUser);

            // Fetch wallet data
            const walletData = await getWallet();

            // Fetch projects
            const projectsData = await getProjects({ view: 'my_projects' });

            const activeCount = projectsData.filter(p =>
                ['in_progress', 'assigned', 'deliverable_submitted'].includes(p.status)
            ).length;

            const completedCount = projectsData.filter(p =>
                p.status === 'completed'
            ).length;

            setStats({
                in_escrow: walletData.in_escrow || 0,
                total_earnings: walletData.total_earnings || 0,
                active_projects: activeCount,
                completed_projects: completedCount
            });

            setRecentProjects(projectsData.slice(0, 3));
        } catch (error) {
            console.error('Failed to fetch dashboard data', error);
        }
    };

    return (
        <div>
            {readiness && (
                <div
                    style={{
                        display: 'grid',
                        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
                        gap: '1rem',
                        background: 'var(--glass-bg)',
                        border: '1px solid var(--glass-border)',
                        borderRadius: '0.75rem',
                        padding: '1rem',
                        marginBottom: '1.25rem'
                    }}
                >
                    <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#10b981', fontWeight: 700 }}>
                            <ShieldCheck size={18} /> Freelancer Readiness
                        </div>
                        <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--text-primary)', marginTop: '0.35rem' }}>
                            {readiness.score}%
                        </div>
                        <div style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', textTransform: 'capitalize' }}>
                            {readiness.level.replace('_', ' ')}
                        </div>
                    </div>
                    <div>
                        <p style={{ margin: 0, color: 'var(--text-secondary)', fontSize: '0.92rem', lineHeight: 1.5 }}>
                            This score helps you understand how ready your profile is before applying. Job proposals are still checked against each project, so keep your skills, proof links, and proposal text specific to the client brief.
                        </p>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.75rem' }}>
                            {Object.entries(readiness.breakdown).map(([key, value]) => (
                                <span key={key} style={{
                                    fontSize: '0.78rem',
                                    color: 'var(--text-secondary)',
                                    background: 'rgba(255,255,255,0.6)',
                                    border: '1px solid var(--glass-border)',
                                    borderRadius: '999px',
                                    padding: '0.25rem 0.55rem',
                                    textTransform: 'capitalize'
                                }}>
                                    {key.replace('_', ' ')} {value}%
                                </span>
                            ))}
                        </div>
                        {readiness.next_actions?.length > 0 && (
                            <button
                                className="btn btn-outline"
                                style={{ marginTop: '0.9rem', padding: '0.45rem 0.8rem', fontSize: '0.86rem' }}
                                onClick={() => navigate('/dashboard/settings')}
                            >
                                Improve Profile <ArrowRight size={15} />
                            </button>
                        )}
                    </div>
                </div>
            )}

            {/* Stats Grid */}
            <div className="stats-grid">
                <div className="stat-card" id="tour-earnings">
                    <div className="stat-header">
                        <span className="stat-title">Total Earnings</span>
                        <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.1)', color: '#10b981' }}>
                            <DollarSign size={20} />
                        </div>
                    </div>
                    <div className="stat-value">KES {parseFloat(stats.total_earnings).toLocaleString()}</div>
                    <div className="stat-trend">Released from Escrow</div>
                </div>

                <div className="stat-card" id="tour-active-jobs">
                    <div className="stat-header">
                        <span className="stat-title">Active Jobs</span>
                        <div className="stat-icon" style={{ background: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6' }}>
                            <Briefcase size={20} />
                        </div>
                    </div>
                    <div className="stat-value">{stats.active_projects}</div>
                    <div className="stat-trend">In Progress</div>
                </div>

                <div className="stat-card" id="tour-escrow">
                    <div className="stat-header">
                        <span className="stat-title">Pending Payment</span>
                        <div className="stat-icon" style={{ background: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b' }}>
                            <Clock size={20} />
                        </div>
                    </div>
                    <div className="stat-value">KES {parseFloat(stats.in_escrow).toLocaleString()}</div>
                    <div className="stat-trend">In Escrow</div>
                </div>

                <div className="stat-card">
                    <div className="stat-header">
                        <span className="stat-title">Completed</span>
                        <div className="stat-icon" style={{ background: 'rgba(139, 92, 246, 0.1)', color: '#8b5cf6' }}>
                            <CheckCircle size={20} />
                        </div>
                    </div>
                    <div className="stat-value">{stats.completed_projects}</div>
                    <div className="stat-trend">Projects</div>
                </div>
            </div>

            {/* Recent Projects Section */}
            <div className="recent-section dashboard-recent-section">
                <div className="recent-header">
                    <h2 className="section-title">Recent Projects</h2>
                    <button
                        className="btn btn-primary"
                        style={{ padding: '0.5rem 1rem', fontSize: '0.9rem' }}
                        onClick={() => navigate('/dashboard/find-work')}
                    >
                        Find Work
                    </button>
                </div>

                {recentProjects.length === 0 ? (
                    <div className="empty-state">
                        <p>You haven't been assigned to any projects yet.</p>
                        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                            Browse available gigs to get started!
                        </p>
                    </div>
                ) : (
                    <div className="dashboard-recent-scroll">
                        {recentProjects.map(project => (
                            <div
                                key={project.id}
                                className="feature-card"
                                style={{ cursor: 'pointer' }}
                                onClick={() => navigate(`/dashboard/projects/${project.id}`)}
                            >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                                    <div>
                                        <h4 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>{project.title}</h4>
                                        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                                            {project.description.substring(0, 100)}...
                                        </p>
                                    </div>
                                    <div style={{
                                        padding: '0.4rem 0.8rem',
                                        borderRadius: '20px',
                                        fontSize: '0.8rem',
                                        fontWeight: '600',
                                        background: project.status === 'completed' ? 'rgba(16, 185, 129, 0.2)' :
                                            'rgba(245, 158, 11, 0.2)',
                                        color: project.status === 'completed' ? '#10b981' : '#f59e0b',
                                        whiteSpace: 'nowrap'
                                    }}>
                                        {project.status.replace('_', ' ').toUpperCase()}
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default FreelancerDashboard;
