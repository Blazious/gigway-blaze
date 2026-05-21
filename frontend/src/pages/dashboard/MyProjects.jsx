import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, Calendar, Eye, Trash2, X } from 'lucide-react';
import { deleteProject, getProjects } from '../../api';

const MyProjects = () => {
    const navigate = useNavigate();
    const [projects, setProjects] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const hiddenStorageKey = `hidden_my_projects_${user.id || 'guest'}`;
    const [hiddenProjectIds, setHiddenProjectIds] = useState(() => {
        try {
            return JSON.parse(localStorage.getItem(hiddenStorageKey) || '[]');
        } catch {
            return [];
        }
    });

    useEffect(() => {
        fetchProjects();
    }, []);

    const fetchProjects = async () => {
        try {
            const data = await getProjects({ view: 'my_projects' });
            setProjects(data.filter(project => !hiddenProjectIds.includes(project.id)));
        } catch (error) {
            console.error("Failed to fetch my projects", error);
        } finally {
            setIsLoading(false);
        }
    };

    const forgetProject = (projectId) => {
        const nextHidden = [...new Set([...hiddenProjectIds, projectId])];
        setHiddenProjectIds(nextHidden);
        localStorage.setItem(hiddenStorageKey, JSON.stringify(nextHidden));
        setProjects(projects.filter(project => project.id !== projectId));
    };

    const handleRemoveProject = async (project) => {
        const canDelete = user.user_type === 'client' && project.status === 'open';
        const action = canDelete ? 'delete' : 'forget';

        if (!window.confirm(`Do you want to ${action} "${project.title}" from this list?`)) {
            return;
        }

        if (canDelete) {
            try {
                await deleteProject(project.id);
                setProjects(projects.filter(item => item.id !== project.id));
                return;
            } catch (error) {
                alert(error.response?.data?.error || 'Could not delete this project. It will be forgotten from your list instead.');
            }
        }

        forgetProject(project.id);
    };

    return (
        <div>
            <h2 className="section-title" style={{ textAlign: 'left', marginBottom: '1.5rem' }}>My Projects</h2>

            {isLoading ? (
                <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}>
                    <Loader2 className="animate-spin" size={40} color="var(--primary)" />
                </div>
            ) : projects.length === 0 ? (
                <div className="empty-state">
                    <p>You don't have any active projects yet.</p>
                </div>
            ) : (
                <div className="project-grid-compact">
                    {projects.map(project => (
                        <div key={project.id} className="project-card-compact">
                            <div className="project-card-header">
                                <span style={{
                                    fontSize: '0.8rem',
                                    padding: '0.2rem 0.55rem',
                                    borderRadius: '20px',
                                    background: project.status === 'in_progress' ? 'rgba(16, 185, 129, 0.2)' : 'rgba(59, 130, 246, 0.2)',
                                    color: project.status === 'in_progress' ? '#10b981' : '#3b82f6'
                                }}>
                                    {project.status.replace('_', ' ').toUpperCase()}
                                </span>
                                <span style={{ color: 'var(--text-secondary)', fontSize: '0.82rem', whiteSpace: 'nowrap' }}>
                                    KES {parseFloat(project.budget).toLocaleString()}
                                </span>
                            </div>

                            <h3 className="project-card-title">
                                {project.title}
                            </h3>
                            <p className="project-card-desc">
                                {project.description}
                            </p>

                            <div style={{ display: 'flex', gap: '1rem', color: 'var(--text-secondary)', fontSize: '0.78rem', marginBottom: '0.75rem' }}>
                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                                    <Calendar size={14} />
                                    <span>{new Date(project.created_at).toLocaleDateString()}</span>
                                </div>
                            </div>

                            <div className="project-card-actions">
                                <button
                                    className="btn btn-outline"
                                    style={{ width: '100%', borderRadius: '0.5rem', padding: '0.55rem 0.75rem' }}
                                    onClick={() => navigate(`/dashboard/projects/${project.id}`)}
                                >
                                    <Eye size={16} /> Open
                                </button>
                                <button
                                    type="button"
                                    className="project-icon-btn"
                                    title={user.user_type === 'client' && project.status === 'open' ? 'Delete project' : 'Forget this project'}
                                    onClick={() => handleRemoveProject(project)}
                                >
                                    {user.user_type === 'client' && project.status === 'open' ? <Trash2 size={16} /> : <X size={16} />}
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default MyProjects;
