import React, { useState, useEffect } from 'react';
import { Loader2, Upload, FileText, CheckCircle, XCircle, AlertCircle, Download, Link as LinkIcon, AlignLeft } from 'lucide-react';
import { getDeliverables, submitDeliverable, approveDeliverable, rejectDeliverable, getEscrowStatus } from '../../api';

const DeliverableTab = ({ projectId, project, onDeliverableUpdate }) => {
    const [deliverables, setDeliverables] = useState([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [escrowStatus, setEscrowStatus] = useState(project?.escrow_status || project?.contract?.escrow?.status || 'pending');
    const [isCheckingEscrow, setIsCheckingEscrow] = useState(false);

    // Submission States
    const [submissionType, setSubmissionType] = useState('file'); // 'file', 'link', 'text'
    const [file, setFile] = useState(null);
    const [linkUrl, setLinkUrl] = useState('');
    const [textContent, setTextContent] = useState('');
    const [description, setDescription] = useState('');

    const [dragActive, setDragActive] = useState(false);
    const [rejectionReason, setRejectionReason] = useState('');
    const [showRejectModal, setShowRejectModal] = useState(null);
    const [expandedText, setExpandedText] = useState({});
    const [manualConfirmationCode, setManualConfirmationCode] = useState('');

    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const userType = user.user_type;
    const isFreelancer = userType === 'freelancer';
    const isClient = userType === 'client';

    useEffect(() => {
        fetchDeliverables();
        fetchEscrowStatus();
    }, [projectId]);

    useEffect(() => {
        const nextStatus = project?.escrow_status || project?.contract?.escrow?.status;
        if (nextStatus) setEscrowStatus(nextStatus);
    }, [project?.escrow_status, project?.contract?.escrow?.status]);

    useEffect(() => {
        if (!isFreelancer || escrowStatus === 'held') return undefined;

        let attempts = 0;
        const interval = setInterval(async () => {
            attempts += 1;
            const status = await fetchEscrowStatus();
            if (status === 'held' || attempts >= 40) {
                clearInterval(interval);
            }
        }, 3000);

        return () => clearInterval(interval);
    }, [isFreelancer, escrowStatus, projectId]);

    const fetchDeliverables = async () => {
        try {
            const data = await getDeliverables(projectId);
            setDeliverables(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error('Failed to fetch deliverables', error);
            setDeliverables([]);
        } finally {
            setIsLoading(false);
        }
    };

    const fetchEscrowStatus = async () => {
        setIsCheckingEscrow(true);
        try {
            const data = await getEscrowStatus(projectId);
            if (data?.status) {
                setEscrowStatus(data.status);
                if (data.status === 'held' && onDeliverableUpdate) {
                    onDeliverableUpdate();
                }
                return data.status;
            }
        } catch (error) {
            if (error.response?.status !== 404) {
                console.error('Failed to fetch escrow status', error);
            }
        } finally {
            setIsCheckingEscrow(false);
        }
        return null;
    };

    const handleFileChange = (e) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
        }
    };

    const handleDrag = (e) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true);
        } else if (e.type === 'dragleave') {
            setDragActive(false);
        }
    };

    const handleDrop = (e) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            setFile(e.dataTransfer.files[0]);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        // Validation
        if (!description.trim()) {
            alert('Please provide a description of the work.');
            return;
        }

        if (submissionType === 'file' && !file) {
            alert('Please choose a file to upload.');
            return;
        }
        if (submissionType === 'link' && !linkUrl.trim()) {
            alert('Please provide an external link.');
            return;
        }
        if (submissionType === 'text' && !textContent.trim()) {
            alert('Please provide the text content.');
            return;
        }

        // Ensure contract exists
        if (!project || !project.contract || !project.contract.id) {
            alert('No active contract found for this project.');
            return;
        }

        setIsSubmitting(true);
        try {
            const formData = new FormData();
            formData.append('submission_type', submissionType);
            formData.append('description', description);
            // formData.append('project', projectId); // Not needed for new API if passing contractId

            if (submissionType === 'file') {
                formData.append('file', file);
            } else if (submissionType === 'link') {
                formData.append('file_url', linkUrl);
            } else if (submissionType === 'text') {
                formData.append('content', textContent);
            }

            // Using contract ID as per new API
            await submitDeliverable(project.contract.id, formData);
            alert('Deliverable submitted successfully!');

            // Clear inputs
            setFile(null);
            setLinkUrl('');
            setTextContent('');
            setDescription('');

            await fetchDeliverables();
            if (onDeliverableUpdate) onDeliverableUpdate();
        } catch (error) {
            console.error('Failed to submit deliverable', error);
            alert(error.response?.data?.error || 'Failed to submit deliverable. Please try again.');
        } finally {
            setIsSubmitting(false);
        }
    };

    const handleApprove = async (deliverableId) => {
        if (!confirm('Are you sure you want to approve this deliverable? This will release the escrow funds to the freelancer.')) {
            return;
        }

        try {
            const storedCode = project?.contract?.escrow?.confirmation_code || project?.contract?.escrow?.mpesa_receipt;
            let codeToUse = storedCode;
            if (!codeToUse) {
                codeToUse = (manualConfirmationCode || '').trim();
                if (!codeToUse) {
                    alert('Enter your M-Pesa confirmation code first (from payment SMS).');
                    return;
                }
            }

            await approveDeliverable(deliverableId, codeToUse);
            alert('Deliverable approved! Funds are being released to the freelancer.');
            await fetchDeliverables();
            if (onDeliverableUpdate) onDeliverableUpdate();
            setManualConfirmationCode('');
        } catch (error) {
            console.error('Failed to approve deliverable', error);
            alert(error.response?.data?.error || 'Failed to approve deliverable. Please try again.');
        }
    };

    const handleReject = async (deliverableId) => {
        if (!rejectionReason.trim()) {
            alert('Please provide a reason for rejection');
            return;
        }

        try {
            await rejectDeliverable(deliverableId, rejectionReason);
            alert('Deliverable rejected. The freelancer can resubmit.');
            setShowRejectModal(null);
            setRejectionReason('');
            await fetchDeliverables();
            if (onDeliverableUpdate) onDeliverableUpdate();
        } catch (error) {
            console.error('Failed to reject deliverable', error);
            alert(error.response?.data?.error || 'Failed to reject deliverable. Please try again.');
        }
    };

    const toggleExpand = (id) => {
        setExpandedText(prev => ({ ...prev, [id]: !prev[id] }));
    };

    const fundsHeld = escrowStatus === 'held' || project?.contract?.payment_status === 'escrowed';
    const projectAllowsSubmission = ['in_progress', 'assigned', 'deliverable_submitted', 'deliverable_approved'].includes((project?.status || '').toLowerCase());
    const actuallyCanSubmit = isFreelancer && fundsHeld && projectAllowsSubmission;

    if (isLoading) {
        return (
            <div style={{ padding: '2rem', textAlign: 'center' }}>
                <Loader2 className="animate-spin" size={32} />
            </div>
        );
    }

    return (
        <div style={{ animation: 'fadeIn 0.3s ease-in-out' }}>
            {/* Freelancer: Submission Form */}
            {isFreelancer && actuallyCanSubmit && (
                <div style={{
                    background: 'var(--glass-bg)',
                    border: '1px solid var(--glass-border)',
                    borderRadius: '1rem',
                    padding: '2rem',
                    marginBottom: '2rem'
                }}>
                    <h3 style={{ fontSize: '1.25rem', marginBottom: '1.5rem' }}>Submit Deliverable</h3>

                    {/* Mode Tabs */}
                    <div style={{
                        display: 'flex',
                        gap: '1rem',
                        marginBottom: '1.5rem',
                        borderBottom: '1px solid var(--glass-border)',
                        paddingBottom: '0.5rem'
                    }}>
                        {[
                            { id: 'file', label: 'Upload File', icon: <Upload size={16} /> },
                            { id: 'link', label: 'External Link', icon: <LinkIcon size={16} /> },
                            { id: 'text', label: 'Rich Text', icon: <AlignLeft size={16} /> }
                        ].map((tab) => (
                            <button
                                key={tab.id}
                                onClick={() => setSubmissionType(tab.id)}
                                style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: '0.5rem',
                                    padding: '0.5rem 1rem',
                                    borderRadius: '0.5rem',
                                    border: 'none',
                                    background: submissionType === tab.id ? 'var(--primary-light)' : 'transparent',
                                    color: submissionType === tab.id ? 'var(--primary)' : 'var(--text-secondary)',
                                    cursor: 'pointer',
                                    fontWeight: submissionType === tab.id ? '600' : '400',
                                    transition: 'all 0.2s ease'
                                }}
                            >
                                {tab.icon}
                                {tab.label}
                            </button>
                        ))}
                    </div>

                    <form onSubmit={handleSubmit}>
                        {/* Conditional Inputs */}
                        {submissionType === 'file' && (
                            <div
                                onDragEnter={handleDrag}
                                onDragLeave={handleDrag}
                                onDragOver={handleDrag}
                                onDrop={handleDrop}
                                style={{
                                    border: `2px dashed ${dragActive ? 'var(--primary)' : 'var(--glass-border)'}`,
                                    borderRadius: '0.5rem',
                                    padding: '2rem',
                                    textAlign: 'center',
                                    marginBottom: '1.5rem',
                                    background: dragActive ? 'rgba(99, 102, 241, 0.05)' : 'transparent',
                                    transition: 'all 0.3s ease',
                                    cursor: 'pointer'
                                }}
                                onClick={() => document.getElementById('file-input').click()}
                            >
                                <Upload size={48} style={{ opacity: 0.5, marginBottom: '1rem' }} />
                                {file ? (
                                    <div>
                                        <p style={{ color: 'var(--primary)', fontWeight: 'bold' }}>{file.name}</p>
                                        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                                            {(file.size / 1024 / 1024).toFixed(2)} MB
                                        </p>
                                    </div>
                                ) : (
                                    <div>
                                        <p style={{ marginBottom: '0.5rem' }}>Drag and drop your file here</p>
                                        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                                            or click to browse
                                        </p>
                                    </div>
                                )}
                                <input
                                    id="file-input"
                                    type="file"
                                    onChange={handleFileChange}
                                    style={{ display: 'none' }}
                                />
                            </div>
                        )}

                        {submissionType === 'link' && (
                            <div style={{ marginBottom: '1.5rem' }}>
                                <label style={{ display: 'block', fontSize: '0.9rem', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
                                    External URL (Google Drive, Figma, Loom, etc.)
                                </label>
                                <input
                                    type="url"
                                    className="auth-input"
                                    placeholder="https://..."
                                    value={linkUrl}
                                    onChange={(e) => setLinkUrl(e.target.value)}
                                    required
                                />
                                <p style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginTop: '0.5rem' }}>
                                    Ensure the client has permission to view this link.
                                </p>
                            </div>
                        )}

                        {submissionType === 'text' && (
                            <div style={{ marginBottom: '1.5rem' }}>
                                <label style={{ display: 'block', fontSize: '0.9rem', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
                                    Rich Text Submission
                                </label>
                                <textarea
                                    className="auth-input"
                                    placeholder="Paste your article, report, or findings here..."
                                    value={textContent}
                                    onChange={(e) => setTextContent(e.target.value)}
                                    rows={8}
                                    required
                                    style={{ resize: 'vertical', minHeight: '200px' }}
                                />
                            </div>
                        )}

                        {/* Description */}
                        <div style={{ marginBottom: '1.5rem' }}>
                            <label style={{ display: 'block', fontSize: '0.9rem', marginBottom: '0.5rem', color: 'var(--text-secondary)' }}>
                                Description of Work Completed
                            </label>
                            <textarea
                                className="auth-input"
                                value={description}
                                onChange={(e) => setDescription(e.target.value)}
                                placeholder="Describe what you've delivered and any important notes..."
                                rows={3}
                                required
                                style={{ resize: 'vertical' }}
                            />
                        </div>

                        <button
                            className="btn btn-primary"
                            type="submit"
                            disabled={isSubmitting}
                            style={{ width: '100%', display: 'flex', justifyContent: 'center', gap: '0.5rem' }}
                        >
                            {isSubmitting ? <Loader2 className="animate-spin" size={18} /> : <CheckCircle size={18} />}
                            Submit Deliverable
                        </button>
                    </form>
                </div>
            )}

            {/* Info Messages */}
            {isFreelancer && !actuallyCanSubmit && (
                <div style={{
                    background: 'rgba(245, 158, 11, 0.1)',
                    border: '1px solid rgba(245, 158, 11, 0.3)',
                    borderRadius: '1rem',
                    padding: '1.5rem',
                    marginBottom: '2rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '1rem'
                }}>
                    <AlertCircle size={24} color="#f59e0b" />
                    <div>
                        <p style={{ fontWeight: 'bold', marginBottom: '0.25rem' }}>Cannot Submit Yet</p>
                        <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                            {!fundsHeld
                                ? isCheckingEscrow
                                    ? 'Checking eConfirm escrow status...'
                                    : 'Waiting for client to deposit funds to escrow.'
                                : 'Project is not in the correct status for deliverable submission.'}
                        </p>
                        {!fundsHeld && (
                            <button
                                type="button"
                                className="btn btn-outline"
                                onClick={fetchEscrowStatus}
                                disabled={isCheckingEscrow}
                                style={{ marginTop: '0.75rem', padding: '0.45rem 0.8rem' }}
                            >
                                {isCheckingEscrow ? 'Checking...' : 'Check Escrow Again'}
                            </button>
                        )}
                    </div>
                </div>
            )}

            {/* Deliverables List */}
            <div>
                {isClient && !(project?.contract?.escrow?.confirmation_code || project?.contract?.escrow?.mpesa_receipt) && (
                    <div style={{
                        background: 'rgba(245, 158, 11, 0.1)',
                        border: '1px solid rgba(245, 158, 11, 0.3)',
                        borderRadius: '1rem',
                        padding: '1rem',
                        marginBottom: '1rem'
                    }}>
                        <p style={{ marginBottom: '0.5rem', fontSize: '0.9rem' }}>
                            M-Pesa confirmation code is required before release.
                        </p>
                        <input
                            className="auth-input"
                            placeholder="Enter M-Pesa confirmation code (e.g. BIG3Z8XQXW8XQ)"
                            value={manualConfirmationCode}
                            onChange={(e) => setManualConfirmationCode(e.target.value)}
                            style={{ width: '100%' }}
                        />
                    </div>
                )}
                <h3 style={{ fontSize: '1.25rem', marginBottom: '1.5rem' }}>
                    {deliverables.length > 0 ? 'Submitted Deliverables' : 'No Deliverables Yet'}
                </h3>

                {deliverables.length === 0 ? (
                    <div style={{
                        background: 'var(--glass-bg)',
                        border: '1px solid var(--glass-border)',
                        borderRadius: '1rem',
                        padding: '3rem',
                        textAlign: 'center',
                        color: 'var(--text-secondary)'
                    }}>
                        <FileText size={48} style={{ opacity: 0.5, marginBottom: '1rem' }} />
                        <p>No deliverables have been submitted yet.</p>
                    </div>
                ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                        {deliverables.map((deliverable) => (
                            <div
                                key={deliverable.id}
                                style={{
                                    background: 'var(--glass-bg)',
                                    border: '1px solid var(--glass-border)',
                                    borderRadius: '1rem',
                                    padding: '1.5rem'
                                }}
                            >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem' }}>
                                    <div style={{ flex: 1 }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                                            {deliverable.submission_type === 'file' && <FileText size={20} />}
                                            {deliverable.submission_type === 'link' && <LinkIcon size={20} />}
                                            {deliverable.submission_type === 'text' && <AlignLeft size={20} />}
                                            <h4 style={{ fontSize: '1.1rem', margin: 0 }}>
                                                {deliverable.submission_type === 'file' ? 'File Deliverable' :
                                                    deliverable.submission_type === 'link' ? 'External Link' : 'Text Content'}
                                            </h4>
                                        </div>
                                        <p style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', margin: 0 }}>
                                            Submitted {new Date(deliverable.submitted_at).toLocaleDateString()}
                                        </p>
                                    </div>
                                    <div style={{
                                        padding: '0.4rem 0.8rem',
                                        borderRadius: '20px',
                                        fontSize: '0.8rem',
                                        fontWeight: '600',
                                        background: deliverable.status === 'approved' ? 'rgba(16, 185, 129, 0.2)' :
                                            deliverable.status === 'rejected' ? 'rgba(239, 68, 68, 0.2)' :
                                                'rgba(245, 158, 11, 0.2)',
                                        color: deliverable.status === 'approved' ? '#10b981' :
                                            deliverable.status === 'rejected' ? '#ef4444' :
                                                '#f59e0b',
                                        border: '1px solid currentColor',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '0.25rem'
                                    }}>
                                        {deliverable.status === 'approved' && <CheckCircle size={14} />}
                                        {deliverable.status === 'rejected' && <XCircle size={14} />}
                                        {deliverable.status === 'submitted' && <AlertCircle size={14} />}
                                        {deliverable.status.toUpperCase()}
                                    </div>
                                </div>

                                <p style={{ marginBottom: '1rem', lineHeight: '1.6', color: 'var(--text-secondary)' }}>
                                    <strong style={{ color: 'var(--text-primary)' }}>Notes: </strong>
                                    {deliverable.description}
                                </p>

                                {/* Render Work Based on Type */}
                                {deliverable.submission_type === 'file' && deliverable.file_url && (
                                    <a
                                        href={`/media/${deliverable.file_url}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="btn"
                                        style={{
                                            display: 'inline-flex',
                                            alignItems: 'center',
                                            gap: '0.5rem',
                                            fontSize: '0.9rem',
                                            marginBottom: '1rem',
                                            background: 'rgba(99, 102, 241, 0.1)',
                                            color: 'var(--primary)',
                                            border: '1px solid var(--primary-light)'
                                        }}
                                    >
                                        <Download size={16} />
                                        Download File
                                    </a>
                                )}

                                {deliverable.submission_type === 'link' && deliverable.file_url && (
                                    <a
                                        href={deliverable.file_url.startsWith('http') ? deliverable.file_url : `https://${deliverable.file_url}`}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="btn"
                                        style={{
                                            display: 'inline-flex',
                                            alignItems: 'center',
                                            gap: '0.5rem',
                                            fontSize: '0.9rem',
                                            marginBottom: '1rem',
                                            background: 'rgba(99, 102, 241, 0.1)',
                                            color: 'var(--primary)',
                                            border: '1px solid var(--primary-light)'
                                        }}
                                    >
                                        <LinkIcon size={16} />
                                        View External Work
                                    </a>
                                )}

                                {deliverable.submission_type === 'text' && deliverable.content && (
                                    <div style={{
                                        background: 'rgba(255, 255, 255, 0.05)',
                                        border: '1px solid var(--glass-border)',
                                        borderRadius: '0.5rem',
                                        padding: '1rem',
                                        marginBottom: '1rem'
                                    }}>
                                        <div style={{
                                            maxHeight: expandedText[deliverable.id] ? 'none' : '150px',
                                            overflow: 'hidden',
                                            position: 'relative',
                                            whiteSpace: 'pre-wrap',
                                            fontSize: '0.95rem'
                                        }}>
                                            {deliverable.content}
                                            {!expandedText[deliverable.id] && deliverable.content.length > 300 && (
                                                <div style={{
                                                    position: 'absolute',
                                                    bottom: 0,
                                                    left: 0,
                                                    right: 0,
                                                    height: '40px',
                                                    background: 'linear-gradient(transparent, var(--bg-primary))',
                                                    pointerEvents: 'none'
                                                }} />
                                            )}
                                        </div>
                                        {deliverable.content.length > 300 && (
                                            <button
                                                onClick={() => toggleExpand(deliverable.id)}
                                                style={{
                                                    background: 'none',
                                                    border: 'none',
                                                    color: 'var(--primary)',
                                                    cursor: 'pointer',
                                                    fontSize: '0.85rem',
                                                    marginTop: '0.5rem',
                                                    fontWeight: '600'
                                                }}
                                            >
                                                {expandedText[deliverable.id] ? 'Show Less' : 'Read More'}
                                            </button>
                                        )}
                                    </div>
                                )}

                                {deliverable.status === 'rejected' && deliverable.rejection_reason && (
                                    <div style={{
                                        background: 'rgba(239, 68, 68, 0.1)',
                                        border: '1px solid rgba(239, 68, 68, 0.3)',
                                        borderRadius: '0.5rem',
                                        padding: '1rem',
                                        marginTop: '1rem'
                                    }}>
                                        <p style={{ fontSize: '0.85rem', fontWeight: 'bold', marginBottom: '0.5rem', color: '#ef4444' }}>
                                            Rejection Reason:
                                        </p>
                                        <p style={{ fontSize: '0.9rem', margin: 0 }}>{deliverable.rejection_reason}</p>
                                    </div>
                                )}

                                {/* Client Actions */}
                                {isClient && deliverable.status === 'submitted' && (
                                    <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
                                        <button
                                            className="btn btn-primary"
                                            onClick={() => handleApprove(deliverable.id)}
                                            style={{ flex: 1, display: 'flex', justifyContent: 'center', gap: '0.5rem' }}
                                        >
                                            <CheckCircle size={18} />
                                            Approve & Release Funds
                                        </button>
                                        <button
                                            className="btn"
                                            onClick={() => setShowRejectModal(deliverable.id)}
                                            style={{
                                                flex: 1,
                                                background: 'rgba(239, 68, 68, 0.1)',
                                                color: '#ef4444',
                                                border: '1px solid rgba(239, 68, 68, 0.3)',
                                                display: 'flex',
                                                justifyContent: 'center',
                                                gap: '0.5rem'
                                            }}
                                        >
                                            <XCircle size={18} />
                                            Reject
                                        </button>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Reject Modal */}
            {showRejectModal && (
                <div style={{
                    position: 'fixed',
                    top: 0,
                    left: 0,
                    right: 0,
                    bottom: 0,
                    background: 'rgba(0, 0, 0, 0.7)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    zIndex: 1000,
                    padding: '1rem'
                }}>
                    <div style={{
                        background: 'var(--bg-primary)',
                        borderRadius: '1rem',
                        padding: '2rem',
                        maxWidth: '500px',
                        width: '100%',
                        border: '1px solid var(--glass-border)'
                    }}>
                        <h3 style={{ fontSize: '1.25rem', marginBottom: '1rem' }}>Reject Deliverable</h3>
                        <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', fontSize: '0.9rem' }}>
                            Please provide a reason for rejecting this deliverable. The freelancer will be able to see this and resubmit.
                        </p>
                        <textarea
                            className="auth-input"
                            value={rejectionReason}
                            onChange={(e) => setRejectionReason(e.target.value)}
                            placeholder="Explain what needs to be improved or changed..."
                            rows={4}
                            style={{ marginBottom: '1.5rem', resize: 'vertical' }}
                        />
                        <div style={{ display: 'flex', gap: '1rem' }}>
                            <button
                                className="btn"
                                onClick={() => {
                                    setShowRejectModal(null);
                                    setRejectionReason('');
                                }}
                                style={{ flex: 1 }}
                            >
                                Cancel
                            </button>
                            <button
                                className="btn btn-primary"
                                onClick={() => handleReject(showRejectModal)}
                                disabled={!rejectionReason.trim()}
                                style={{
                                    flex: 1,
                                    background: '#ef4444',
                                    borderColor: '#ef4444'
                                }}
                            >
                                Reject Deliverable
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default DeliverableTab;
