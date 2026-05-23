import React, { useState } from 'react';
import { Loader2, DollarSign, Send, ShieldCheck } from 'lucide-react';
import { createProposal } from '../../api';

const getErrorMessage = (data) => {
    if (!data) return null;
    if (typeof data === 'string') return data;
    if (Array.isArray(data)) return data.join(' ');
    if (typeof data === 'object') {
        return Object.entries(data)
            .map(([key, value]) => `${key}: ${getErrorMessage(value)}`)
            .join(' ');
    }
    return null;
};

const ApplyModal = ({ isOpen, onClose, project, onSuccess }) => {
    const [formData, setFormData] = useState({
        cover_letter: '',
        bid_amount: project?.budget || '',
        relevant_experience: '',
        qualification_summary: '',
        portfolio_url: ''
    });
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState('');

    if (!isOpen || !project) return null;

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        setError('');
        try {
            await createProposal({
                project: project.id,
                ...formData
            });
            onSuccess();
            onClose();
        } catch (error) {
            console.error("Failed to submit proposal", error);
            const verificationError = error.response?.data?.verification;
            const responseError = getErrorMessage(error.response?.data);
            const genericError = error.response?.data?.error || "Failed to submit (you may have already applied).";
            setError(verificationError || responseError || genericError);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
            background: 'rgba(0,0,0,0.7)', display: 'flex', alignItems: 'center', justifyContent: 'center',
            zIndex: 1000, backdropFilter: 'blur(5px)'
        }}>
            <div style={{
                background: 'var(--card-bg)', border: '1px solid var(--glass-border)',
                borderRadius: '1rem', padding: '2rem', width: '90%', maxWidth: '500px',
                position: 'relative', maxHeight: '90vh', overflowY: 'auto'
            }}>
                <h2 className="section-title" style={{ textAlign: 'left', marginBottom: '1rem' }}>Apply to {project.title}</h2>
                <div style={{
                    display: 'flex', alignItems: 'flex-start', gap: '0.75rem',
                    color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '1.25rem'
                }}>
                    <ShieldCheck size={20} style={{ color: '#10b981', flexShrink: 0, marginTop: '0.1rem' }} />
                    <span>GigWay will score your proposal fit for the client, but low scores will not block your application.</span>
                </div>
                {error && (
                    <div style={{
                        background: 'rgba(239, 68, 68, 0.12)', border: '1px solid rgba(239, 68, 68, 0.35)',
                        color: '#ef4444', borderRadius: '0.5rem', padding: '0.75rem', marginBottom: '1rem',
                        fontSize: '0.9rem'
                    }}>
                        {error}
                    </div>
                )}

                <form onSubmit={handleSubmit}>
                    <div className="form-group">
                        <label className="form-label">Your Bid (KES)</label>
                        <div className="input-group">
                            <DollarSign size={20} />
                            <input
                                type="number"
                                className="form-input"
                                min="100"
                                value={formData.bid_amount}
                                onChange={(e) => setFormData({ ...formData, bid_amount: e.target.value })}
                                required
                            />
                        </div>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Cover Letter</label>
                        <textarea
                            className="form-input"
                            rows="4"
                            placeholder="Why are you a good fit?"
                            value={formData.cover_letter}
                            onChange={(e) => setFormData({ ...formData, cover_letter: e.target.value })}
                            required
                        ></textarea>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Relevant Experience</label>
                        <textarea
                            className="form-input"
                            rows="3"
                            placeholder="Mention similar work, tools used, and measurable outcomes."
                            value={formData.relevant_experience}
                            onChange={(e) => setFormData({ ...formData, relevant_experience: e.target.value })}
                            required
                        ></textarea>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Qualifications / Competencies</label>
                        <textarea
                            className="form-input"
                            rows="3"
                            placeholder="List certifications, training, years of practice, or core competencies."
                            value={formData.qualification_summary}
                            onChange={(e) => setFormData({ ...formData, qualification_summary: e.target.value })}
                            required
                        ></textarea>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Portfolio or Proof Link</label>
                        <input
                            type="url"
                            className="form-input"
                            placeholder="https://..."
                            value={formData.portfolio_url}
                            onChange={(e) => setFormData({ ...formData, portfolio_url: e.target.value })}
                        />
                    </div>

                    <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end', marginTop: '1.5rem' }}>
                        <button type="button" onClick={onClose} className="btn btn-outline">Cancel</button>
                        <button type="submit" className="btn btn-primary" disabled={isLoading}>
                            {isLoading ? <Loader2 className="animate-spin" size={18} /> : <Send size={18} />}
                            Submit Proposal
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default ApplyModal;
