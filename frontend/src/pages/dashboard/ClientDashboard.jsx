import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { DollarSign, Briefcase, Clock, CheckCircle } from 'lucide-react';
import { getWallet, getProjects } from '../../api';

const ClientDashboard = () => {
    const navigate = useNavigate();
    // Reusing wallet API to get simple stats for now
    const [stats, setStats] = useState({
        in_escrow: 0,
        total_spent: 0, // Using total_earnings from wallet endpoint as proxy for 'spent' or released
        active_projects: 0,
        completed_projects: 0
    });
    const [recentProjects, setRecentProjects] = useState([]);

    useEffect(() => {
        fetchDashboardData();
    }, []);

    const fetchDashboardData = async () => {
        try {
            const walletData = await getWallet();
            const projectsData = await getProjects();

            const activeCount = projectsData.filter(p =>
                ['assigned', 'in_progress', 'deliverable_submitted'].includes(p.status)
            ).length;

            const completedCount = projectsData.filter(p =>
                p.status === 'completed'
            ).length;

            setStats({
                in_escrow: walletData.in_escrow,
                total_spent: walletData.total_earnings, // Released funds = spent by client
                active_projects: activeCount,
                completed_projects: completedCount
            });

            setRecentProjects(projectsData.slice(0, 3));
        } catch (e) {
            console.error(e);
        }
    };

    return (
        <div style={{ animation: 'fadeIn 0.5s ease-out' }}>
            {/* Stats Grid */}
            <div className="stats-grid">
                <div className="stat-card" id="tour-total-spent">
                    <div className="stat-header">
                        <span className="stat-title">Total Spent</span>
                        <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.1)', color: '#10b981' }}>
                            <DollarSign size={20} />
                        </div>
                    </div>
                    <div className="stat-value">KES {parseFloat(stats.total_spent).toLocaleString()}</div>
                    <div className="stat-trend">Released to Freelancers</div>
                </div>

                <div className="stat-card" id="tour-client-escrow">
                    <div className="stat-header">
                        <span className="stat-title">Funds in Escrow</span>
                        <div className="stat-icon" style={{ background: 'rgba(59, 130, 246, 0.1)', color: '#3b82f6' }}>
                            <Briefcase size={20} />
                        </div>
                    </div>
                    <div className="stat-value">KES {parseFloat(stats.in_escrow).toLocaleString()}</div>
                    <div className="stat-trend" style={{ color: '#3b82f6' }}>Active Contracts</div>
                </div>

                <div className="stat-card" id="tour-active-projects">
                    <div className="stat-header">
                        <span className="stat-title">Active Projects</span>
                        <div className="stat-icon" style={{ background: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b' }}>
                            <Clock size={20} />
                        </div>
                    </div>
                    <div className="stat-value">{stats.active_projects}</div>
                    <div className="stat-trend" style={{ color: '#f59e0b' }}>In Progress</div>
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

            {/* Recent Activity Section */}
            <div className="recent-section dashboard-recent-section">
                <h3 className="section-title" style={{ fontSize: '1.25rem', marginBottom: '1.5rem', textAlign: 'left' }}>Recent Project Activity</h3>
                <div className="dashboard-recent-scroll">
                    {recentProjects.length === 0 ? (
                        <div className="activity-item">
                            <div className="activity-content">
                                <p style={{ color: 'var(--text-secondary)' }}>No recent activity to show.</p>
                            </div>
                        </div>
                    ) : (
                        recentProjects.map(project => (
                            <div
                                key={project.id}
                                className="feature-card"
                                style={{ cursor: 'pointer', marginBottom: '1rem' }}
                                onClick={() => navigate(`/dashboard/projects/${project.id}`)}
                            >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
                                    <div>
                                        <h4 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>{project.title}</h4>
                                        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                                            Budget: KES {parseFloat(project.budget).toLocaleString()}
                                        </p>
                                    </div>
                                    <div style={{
                                        padding: '0.4rem 0.8rem',
                                        borderRadius: '20px',
                                        fontSize: '0.8rem',
                                        fontWeight: '600',
                                        background: project.status === 'completed' ? 'rgba(16, 185, 129, 0.2)' :
                                            project.status === 'open' ? 'rgba(59, 130, 246, 0.2)' :
                                                'rgba(245, 158, 11, 0.2)',
                                        color: project.status === 'completed' ? '#10b981' :
                                            project.status === 'open' ? '#3b82f6' :
                                                '#f59e0b',
                                        whiteSpace: 'nowrap'
                                    }}>
                                        {project.status.replace('_', ' ').toUpperCase()}
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
};

export default ClientDashboard;
