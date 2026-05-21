import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, Search, Eye, X, ShieldCheck } from 'lucide-react';
import { getProjects } from '../../api';

const FindWork = () => {
    const navigate = useNavigate();
    const [projects, setProjects] = useState([]);
    const [hiddenProjectIds, setHiddenProjectIds] = useState(() => {
        try {
            return JSON.parse(localStorage.getItem('hidden_find_work_projects') || '[]');
        } catch {
            return [];
        }
    });
    const [isLoading, setIsLoading] = useState(true);
    const [filters, setFilters] = useState({
        search: '',
        min_budget: '',
        max_budget: ''
    });

    useEffect(() => {
        const delayDebounceFn = setTimeout(() => {
            fetchProjects();
        }, 500); // 500ms debounce

        return () => clearTimeout(delayDebounceFn);
    }, [filters]);

    const fetchProjects = async () => {
        setIsLoading(true);
        try {
            const data = await getProjects({
                view: 'find_work',
                ...filters
            });
            setProjects(data.filter(project => !hiddenProjectIds.includes(project.id)));
        } catch (error) {
            console.error("Failed to search projects", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleFilterChange = (e) => {
        setFilters({ ...filters, [e.target.name]: e.target.value });
    };

    const forgetProject = (projectId) => {
        const nextHidden = [...new Set([...hiddenProjectIds, projectId])];
        setHiddenProjectIds(nextHidden);
        localStorage.setItem('hidden_find_work_projects', JSON.stringify(nextHidden));
        setProjects(projects.filter(project => project.id !== projectId));
    };

    return (
        <div>
            <h2 className="section-title" style={{ textAlign: 'left', marginBottom: '1.5rem' }}>Find Work</h2>

            <div style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.75rem',
                border: '1px solid var(--glass-border)',
                background: 'var(--glass-bg)',
                borderRadius: '0.75rem',
                padding: '1rem',
                marginBottom: '1rem',
                color: 'var(--text-secondary)',
                fontSize: '0.92rem',
                lineHeight: 1.5
            }}>
                <ShieldCheck size={20} style={{ color: '#10b981', flexShrink: 0, marginTop: '0.1rem' }} />
                <span>
                    Before you apply, GigWay checks whether your profile and proposal match the job. Add real proof links, keep your skills current, and mention the client's actual requirements in your cover letter.
                </span>
            </div>

            {/* Search & Filters */}
            <div style={{
                background: 'var(--glass-bg)',
                border: '1px solid var(--glass-border)',
                padding: '1.5rem',
                borderRadius: '1rem',
                marginBottom: '2rem'
            }}>
                <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
                    <div style={{ flex: 2, position: 'relative' }}>
                        <Search size={20} style={{ position: 'absolute', left: '1rem', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
                        <input
                            type="text"
                            name="search"
                            placeholder="Search for keywords (e.g. Web Design)"
                            className="form-input"
                            style={{ paddingLeft: '3rem' }}
                            value={filters.search}
                            onChange={handleFilterChange}
                        />
                    </div>
                    <div style={{ flex: 1, display: 'flex', gap: '0.5rem' }}>
                        <input
                            type="number"
                            name="min_budget"
                            placeholder="Min Budget"
                            className="form-input"
                            value={filters.min_budget}
                            onChange={handleFilterChange}
                        />
                        <input
                            type="number"
                            name="max_budget"
                            placeholder="Max Budget"
                            className="form-input"
                            value={filters.max_budget}
                            onChange={handleFilterChange}
                        />
                    </div>
                </div>
            </div>

            {isLoading ? (
                <div style={{ display: 'flex', justifyContent: 'center', padding: '4rem' }}>
                    <Loader2 className="animate-spin" size={40} color="var(--primary)" />
                </div>
            ) : projects.length === 0 ? (
                <div className="empty-state">
                    <p>No projects found matching your criteria.</p>
                </div>
            ) : (
                <div className="project-grid-compact">
                    {projects.map(project => (
                        <div key={project.id} className="project-card-compact">
                            <div className="project-card-header">
                                <span className="project-card-meta">
                                    Posted by {project.client_name || 'Client'}
                                </span>
                                <span style={{ color: '#10b981', fontWeight: '700', fontSize: '0.88rem', whiteSpace: 'nowrap' }}>
                                    KES {parseFloat(project.budget).toLocaleString()}
                                </span>
                            </div>

                            <h3 className="project-card-title">
                                {project.title}
                            </h3>

                            <p className="project-card-desc">
                                {project.description}
                            </p>

                            <div className="project-card-actions">
                                <button
                                    className="btn btn-primary"
                                    style={{ width: '100%', borderRadius: '0.5rem', padding: '0.55rem 0.75rem' }}
                                    onClick={() => navigate(`/dashboard/projects/${project.id}`)}
                                >
                                    <Eye size={16} /> View
                                </button>
                                <button
                                    type="button"
                                    className="project-icon-btn"
                                    title="Forget this project"
                                    onClick={() => forgetProject(project.id)}
                                >
                                    <X size={16} />
                                </button>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default FindWork;
