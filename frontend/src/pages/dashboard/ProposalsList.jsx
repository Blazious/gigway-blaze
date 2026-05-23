import React, { useState, useEffect } from 'react';
import { Loader2, CheckCircle, User, ShieldCheck, AlertTriangle, ExternalLink } from 'lucide-react';
import { getProposals, acceptProposal } from '../../api';

const ProposalsList = ({ projectId }) => {
    const [proposals, setProposals] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [statusMap, setStatusMap] = useState({}); // To track hiring process

    useEffect(() => {
        fetchProposals();
    }, [projectId]);

    const fetchProposals = async () => {
        try {
            const data = await getProposals(projectId);
            setProposals(data);
        } catch (error) {
            console.error("Failed to load proposals", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleHire = async (proposalId) => {
        console.log('handleHire called with proposalId:', proposalId);

        if (!window.confirm("Are you sure you want to hire this freelancer? This will start the contract.")) {
            console.log('User cancelled hire');
            return;
        }

        console.log('User confirmed, proceeding with hire...');
        setStatusMap({ ...statusMap, [proposalId]: 'hiring' });

        try {
            console.log('Calling acceptProposal API...');
            const response = await acceptProposal(proposalId);
            console.log('API response:', response);

            alert('Freelancer hired successfully! Refreshing page...');
            // Refresh to show status update
            window.location.reload();
        } catch (error) {
            console.error("Hiring failed:", error);
            console.error("Error details:", error.response?.data);
            alert(`Failed to hire freelancer: ${error.response?.data?.error || error.message}`);
            setStatusMap({ ...statusMap, [proposalId]: 'failed' });
        }
    };

    const getVerificationBadge = (proposal) => {
        if (proposal.verification_status === 'verified') {
            return {
                icon: <ShieldCheck size={16} />,
                label: `Verified ${proposal.verification_score}%`,
                color: '#10b981',
                bg: 'rgba(16, 185, 129, 0.15)'
            };
        }

        return {
            icon: <AlertTriangle size={16} />,
            label: `Needs review ${proposal.verification_score || 0}%`,
            color: '#f59e0b',
            bg: 'rgba(245, 158, 11, 0.15)'
        };
    };

    if (isLoading) return <div style={{ textAlign: 'center', padding: '2rem' }}><Loader2 className="animate-spin" /></div>;

    if (proposals.length === 0) {
        return (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)', background: 'var(--glass-bg)', borderRadius: '1rem', border: '1px solid var(--glass-border)' }}>
                <User size={48} style={{ opacity: 0.5, marginBottom: '1rem' }} />
                <p>No proposals yet.</p>
            </div>
        );
    }

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem', animation: 'fadeIn 0.3s ease-in-out' }}>
            {proposals.map((proposal) => (
                <div key={proposal.id} style={{
                    background: 'var(--glass-bg)',
                    border: '1px solid var(--glass-border)',
                    borderRadius: '1rem',
                    padding: '1.5rem',
                    display: 'flex',
                    alignItems: 'flex-start',
                    justifyContent: 'space-between'
                }}>
                    <div style={{ flex: 1, paddingRight: '1rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                            <h4 style={{ margin: 0, fontSize: '1.1rem' }}>{proposal.freelancer_name}</h4>
                            <span style={{
                                fontSize: '0.8rem', padding: '0.2rem 0.5rem', borderRadius: '10px',
                                background: 'rgba(59, 130, 246, 0.2)', color: '#3b82f6'
                            }}>Bid: KES {parseFloat(proposal.bid_amount).toLocaleString()}</span>
                            {(() => {
                                const badge = getVerificationBadge(proposal);
                                return (
                                    <span style={{
                                        display: 'inline-flex', alignItems: 'center', gap: '0.3rem',
                                        fontSize: '0.8rem', padding: '0.2rem 0.5rem', borderRadius: '10px',
                                        background: badge.bg, color: badge.color
                                    }}>
                                        {badge.icon} {badge.label}
                                    </span>
                                );
                            })()}
                            {proposal.freelancer_readiness && (
                                <span style={{
                                    fontSize: '0.8rem', padding: '0.2rem 0.5rem', borderRadius: '10px',
                                    background: 'rgba(15, 23, 42, 0.08)', color: 'var(--text-secondary)',
                                    textTransform: 'capitalize'
                                }}>
                                    Readiness {proposal.freelancer_readiness.score}% · {proposal.freelancer_readiness.level.replace('_', ' ')}
                                </span>
                            )}
                        </div>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', whiteSpace: 'pre-wrap' }}>{proposal.cover_letter}</p>
                        {proposal.relevant_experience && (
                            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', whiteSpace: 'pre-wrap', marginTop: '0.5rem' }}>
                                <strong style={{ color: 'var(--text-primary)' }}>Experience:</strong> {proposal.relevant_experience}
                            </p>
                        )}
                        {proposal.qualification_summary && (
                            <p style={{ color: 'var(--text-secondary)', fontSize: '0.85rem', whiteSpace: 'pre-wrap', marginTop: '0.5rem' }}>
                                <strong style={{ color: 'var(--text-primary)' }}>Competencies:</strong> {proposal.qualification_summary}
                            </p>
                        )}
                        {proposal.portfolio_url && (
                            <a
                                href={proposal.portfolio_url}
                                target="_blank"
                                rel="noreferrer"
                                style={{ display: 'inline-flex', alignItems: 'center', gap: '0.35rem', color: 'var(--primary)', fontSize: '0.85rem', marginTop: '0.5rem' }}
                            >
                                <ExternalLink size={14} /> Proof link
                            </a>
                        )}
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>Applied: {new Date(proposal.created_at).toLocaleDateString()}</div>
                    </div>

                    <div>
                        {proposal.status === 'accepted' ? (
                            <div style={{ color: '#10b981', display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 'bold' }}>
                                <CheckCircle size={20} /> Hired
                            </div>
                        ) : (
                            <button
                                className="btn btn-primary"
                                style={{
                                    padding: '0.5rem 1rem',
                                    fontSize: '0.9rem',
                                    cursor: 'pointer',
                                    pointerEvents: 'auto'
                                }}
                                onClick={(e) => {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    console.log('Hire button clicked for proposal:', proposal.id);
                                    handleHire(proposal.id);
                                }}
                                disabled={statusMap[proposal.id] === 'hiring'}
                                type="button"
                                title={proposal.verification_status !== 'verified' ? 'Score is advisory. You can still hire at your discretion.' : 'Hire freelancer'}
                            >
                                {statusMap[proposal.id] === 'hiring' ? <Loader2 className="animate-spin" size={16} /> : 'Hire'}
                            </button>
                        )}
                    </div>
                </div>
            ))}
        </div>
    );
};

export default ProposalsList;
