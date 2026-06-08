import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Loader2, ArrowLeft, FileText, ShieldCheck, Briefcase, Star } from 'lucide-react';
import { getProject, submitProjectReview } from '../../api';
import GigWayLoader from '../../components/GigWayLoader';
import ContractTab from './ContractTab';
import DeliverableTab from './DeliverableTab';
import ApplyModal from './ApplyModal';
import ProposalsList from './ProposalsList';

const ProjectDetails = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [project, setProject] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('overview');
    const [isApplyModalOpen, setIsApplyModalOpen] = useState(false);
    const [reviewForm, setReviewForm] = useState({ rating: 5, comment: '' });
    const [isReviewSubmitting, setIsReviewSubmitting] = useState(false);

    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const isClient = user.user_type === 'client';
    const projectClientId = project?.client?.id || project?.client;
    const isOwner = isClient && project && projectClientId === user.id;

    useEffect(() => {
        fetchProjectDetails();
    }, [id]);

    const fetchProjectDetails = async () => {
        try {
            const data = await getProject(id);
            setProject(data);
            if (data.review) {
                setReviewForm({
                    rating: data.review.rating || 5,
                    comment: data.review.comment || ''
                });
            }
        } catch (error) {
            console.error("Failed to fetch project details", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleReviewSubmit = async (e) => {
        e.preventDefault();
        setIsReviewSubmitting(true);
        try {
            const review = await submitProjectReview(project.id, reviewForm);
            setProject({ ...project, review });
            alert('Review saved successfully.');
        } catch (error) {
            alert(error.response?.data?.error || 'Failed to save review.');
        } finally {
            setIsReviewSubmitting(false);
        }
    };

    const renderStars = (rating, interactive = false) => (
        <div style={{ display: 'flex', gap: '0.25rem', alignItems: 'center' }}>
            {[1, 2, 3, 4, 5].map(value => (
                <button
                    key={value}
                    type="button"
                    onClick={() => interactive && setReviewForm({ ...reviewForm, rating: value })}
                    disabled={!interactive}
                    aria-label={`${value} star${value > 1 ? 's' : ''}`}
                    style={{
                        background: 'none',
                        border: 'none',
                        padding: 0,
                        cursor: interactive ? 'pointer' : 'default',
                        color: value <= rating ? '#f59e0b' : 'var(--glass-border)',
                        display: 'inline-flex'
                    }}
                >
                    <Star size={22} fill="currentColor" />
                </button>
            ))}
        </div>
    );

    if (isLoading) {
        return <GigWayLoader label="Opening project workspace" />;
    }

    if (!project) {
        return <div style={{ padding: '2rem', textAlign: 'center' }}>Project not found.</div>;
    }

    return (
        <div>
            {/* Header */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '2rem' }}>
                <button
                    onClick={() => navigate(-1)}
                    style={{ background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer', padding: '0.5rem' }}
                >
                    <ArrowLeft size={24} />
                </button>
                <div>
                    <h2 className="section-title" style={{ margin: 0, textAlign: 'left' }}>{project.title}</h2>
                    <span style={{
                        fontSize: '0.85rem',
                        color: 'var(--text-secondary)'
                    }}>
                        Posted by {project.client_name || 'Client'}
                    </span>
                </div>
            </div>

            {/* Tabs */}
            <div style={{
                display: 'flex',
                gap: '2rem',
                borderBottom: '1px solid var(--glass-border)',
                marginBottom: '2rem',
                paddingBottom: '0.5rem'
            }}>
                <button
                    onClick={() => setActiveTab('overview')}
                    style={{
                        background: 'none',
                        border: 'none',
                        color: activeTab === 'overview' ? 'var(--primary)' : 'var(--text-secondary)',
                        fontWeight: activeTab === 'overview' ? 'bold' : 'normal',
                        padding: '0.5rem 0',
                        cursor: 'pointer',
                        position: 'relative',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem'
                    }}
                >
                    <Briefcase size={18} /> Overview
                    {activeTab === 'overview' && (
                        <div style={{ position: 'absolute', bottom: '-0.6rem', left: 0, width: '100%', height: '2px', background: 'var(--primary)' }} />
                    )}
                </button>

                <button
                    onClick={() => setActiveTab('contract')}
                    style={{
                        background: 'none',
                        border: 'none',
                        color: activeTab === 'contract' ? 'var(--primary)' : 'var(--text-secondary)',
                        fontWeight: activeTab === 'contract' ? 'bold' : 'normal',
                        padding: '0.5rem 0',
                        cursor: 'pointer',
                        position: 'relative',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem'
                    }}
                >
                    <ShieldCheck size={18} /> Contract
                    {activeTab === 'contract' && (
                        <div style={{ position: 'absolute', bottom: '-0.6rem', left: 0, width: '100%', height: '2px', background: 'var(--primary)' }} />
                    )}
                </button>

                <button
                    onClick={() => setActiveTab('deliverables')}
                    style={{
                        background: 'none',
                        border: 'none',
                        color: activeTab === 'deliverables' ? 'var(--primary)' : 'var(--text-secondary)',
                        fontWeight: activeTab === 'deliverables' ? 'bold' : 'normal',
                        padding: '0.5rem 0',
                        cursor: 'pointer',
                        position: 'relative',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem'
                    }}
                >
                    <FileText size={18} /> Deliverables
                    {activeTab === 'deliverables' && (
                        <div style={{ position: 'absolute', bottom: '-0.6rem', left: 0, width: '100%', height: '2px', background: 'var(--primary)' }} />
                    )}
                </button>

                {/* Proposals Tab for Clients */}
                {isClient && (
                    <button
                        onClick={() => setActiveTab('proposals')}
                        style={{
                            background: 'none',
                            border: 'none',
                            color: activeTab === 'proposals' ? 'var(--primary)' : 'var(--text-secondary)',
                            fontWeight: activeTab === 'proposals' ? 'bold' : 'normal',
                            padding: '0.5rem 0',
                            cursor: 'pointer',
                            position: 'relative',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem'
                        }}
                    >
                        <Briefcase size={18} /> Proposals
                        {activeTab === 'proposals' && (
                            <div style={{ position: 'absolute', bottom: '-0.6rem', left: 0, width: '100%', height: '2px', background: 'var(--primary)' }} />
                        )}
                    </button>
                )}
            </div>

            {/* Tab Content */}
            <div style={{ textAlign: 'left' }}>
                {activeTab === 'overview' && (
                    <div style={{ animation: 'fadeIn 0.3s ease-in-out' }}>
                        <div className="feature-card" style={{ marginBottom: '2rem' }}>
                            <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem', borderBottom: '1px solid var(--glass-border)', paddingBottom: '0.5rem' }}>Description</h3>
                            <p style={{ lineHeight: '1.6', color: 'var(--text-secondary)', whiteSpace: 'pre-wrap' }}>{project.description}</p>
                        </div>

                        <div className="feature-card">
                            <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem', borderBottom: '1px solid var(--glass-border)', paddingBottom: '0.5rem' }}>Details</h3>
                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1.5rem' }}>
                                <div>
                                    <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Budget</div>
                                    <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#10b981' }}>KES {parseFloat(project.budget).toLocaleString()}</div>
                                </div>
                                <div>
                                    <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Status</div>
                                    <div style={{ textTransform: 'capitalize' }}>{project.status.replace('_', ' ')}</div>
                                </div>
                                <div>
                                    <div style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>Timeline</div>
                                    <div>{project.timeline || 'Not specified'}</div>
                                </div>
                            </div>
                        </div>

                        {project.status === 'completed' && (
                            <div className="feature-card" style={{ marginTop: '2rem' }}>
                                <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem', borderBottom: '1px solid var(--glass-border)', paddingBottom: '0.5rem' }}>
                                    Client Review
                                </h3>

                                {project.review ? (
                                    <div>
                                        {renderStars(project.review.rating)}
                                        {project.review.comment ? (
                                            <p style={{ color: 'var(--text-secondary)', lineHeight: 1.6, whiteSpace: 'pre-wrap', marginTop: '0.85rem' }}>
                                                {project.review.comment}
                                            </p>
                                        ) : (
                                            <p style={{ color: 'var(--text-secondary)', marginTop: '0.85rem' }}>No written comment.</p>
                                        )}
                                    </div>
                                ) : (
                                    <p style={{ color: 'var(--text-secondary)', marginBottom: '1rem' }}>
                                        No review has been left yet.
                                    </p>
                                )}

                                {isOwner && (
                                    <form onSubmit={handleReviewSubmit} style={{ marginTop: '1.25rem' }}>
                                        <label style={{ display: 'block', fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
                                            Rating
                                        </label>
                                        {renderStars(reviewForm.rating, true)}

                                        <label style={{ display: 'block', fontSize: '0.9rem', color: 'var(--text-secondary)', marginTop: '1rem', marginBottom: '0.5rem' }}>
                                            Feedback
                                        </label>
                                        <textarea
                                            className="form-input"
                                            rows="4"
                                            value={reviewForm.comment}
                                            onChange={(e) => setReviewForm({ ...reviewForm, comment: e.target.value })}
                                            placeholder="Share clear feedback about the quality, communication, and delivery."
                                            style={{ resize: 'vertical' }}
                                        />
                                        <button
                                            type="submit"
                                            className="btn btn-primary"
                                            disabled={isReviewSubmitting}
                                            style={{ marginTop: '1rem' }}
                                        >
                                            {isReviewSubmitting ? <Loader2 className="animate-spin" size={18} /> : <Star size={18} />}
                                            {project.review ? 'Update Review' : 'Leave Review'}
                                        </button>
                                    </form>
                                )}
                            </div>
                        )}

                        {/* Apply Button for Freelancers */}
                        {!isClient && project.status === 'open' && (
                            <button
                                className="btn btn-primary"
                                style={{ marginTop: '2rem', width: '100%' }}
                                onClick={() => setIsApplyModalOpen(true)}
                            >
                                Apply for this Job
                            </button>
                        )}
                    </div>
                )}

                {activeTab === 'contract' && (
                    <ContractTab projectId={id} />
                )}

                {activeTab === 'deliverables' && (
                    <DeliverableTab
                        projectId={id}
                        project={project}
                        onDeliverableUpdate={fetchProjectDetails}
                    />
                )}

                {activeTab === 'proposals' && (
                    <ProposalsList projectId={id} />
                )}
            </div>

            <ApplyModal
                isOpen={isApplyModalOpen}
                onClose={() => setIsApplyModalOpen(false)}
                project={project}
                onSuccess={() => alert("Proposal submitted successfully!")}
            />
        </div>
    );
};

export default ProjectDetails;
