import React, { useState, useEffect } from 'react';
import { Loader2, FileSignature, CheckCircle, AlertTriangle, Download } from 'lucide-react';
import { getContract, signContract, initiateEscrowDeposit, getEscrowStatus } from '../../api';

const ContractTab = ({ projectId }) => {
    const [contract, setContract] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isSigning, setIsSigning] = useState(false);
    const [isDepositing, setIsDepositing] = useState(false);
    const [error, setError] = useState(null);
    const [phone, setPhone] = useState(() => {
        try {
            return (JSON.parse(localStorage.getItem('user') || '{}').phone_number || '').trim();
        } catch {
            return '';
        }
    });
    const [escrowStatus, setEscrowStatus] = useState(null);
    const [isPolling, setIsPolling] = useState(false);
    const [depositMessage, setDepositMessage] = useState(null);
    const user = JSON.parse(localStorage.getItem('user') || '{}');
    const userType = user.user_type;

    useEffect(() => {
        if (window.escrowPollInterval) {
            clearInterval(window.escrowPollInterval);
            window.escrowPollInterval = null;
        }
        fetchContract();
        fetchEscrowStatus();
    }, [projectId]);

    useEffect(() => {
        if (escrowStatus?.status === 'pending' && !isPolling && (window.escrowPollInterval == null)) {
            startPolling();
        }
    }, [escrowStatus?.status, isPolling]);

    useEffect(() => {
        return () => {
            if (window.escrowPollInterval) clearInterval(window.escrowPollInterval);
        };
    }, []);

    const fetchContract = async () => {
        try {
            const data = await getContract(projectId);
            setContract(data);
        } catch (err) {
            if (err.response && err.response.status === 404) {
                setError("No contract found. This project might still be open or not assigned.");
            } else {
                setError("Failed to load contract details.");
            }
        } finally {
            setIsLoading(false);
        }
    };

    const fetchEscrowStatus = async () => {
        try {
            const data = await getEscrowStatus(projectId);
            setEscrowStatus(data);

            if (data.status === 'held') {
                setIsPolling(false);
                if (window.escrowPollInterval) {
                    clearInterval(window.escrowPollInterval);
                    window.escrowPollInterval = null;
                }
                setDepositMessage(null);
                await fetchContract();
            }
        } catch (err) {
            if (err.response?.status !== 404) console.log('Escrow status fetch:', err?.message);
        }
    };

    const startPolling = () => {
        setIsPolling(true);
        let pollCount = 0;
        const maxPolls = 40;

        window.escrowPollInterval = setInterval(async () => {
            pollCount++;
            await fetchEscrowStatus();

            if (pollCount >= maxPolls) {
                clearInterval(window.escrowPollInterval);
                window.escrowPollInterval = null;
                setIsPolling(false);
            }
        }, 3000);
    };

    const handleSign = async () => {
        setIsSigning(true);
        try {
            const displayName = user.company_name || user.email.split('@')[0].split(/[._]/).map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(' ');
            const signatureData = { signature: displayName };
            // Uses contract.id
            await signContract(contract.id, signatureData);
            await fetchContract();
        } catch (err) {
            console.error("Signing failed", err);
            setError("Failed to sign contract. Please try again.");
        } finally {
            setIsSigning(false);
        }
    };

    const handleDeposit = async (e) => {
        e.preventDefault();
        setIsDepositing(true);
        setError(null);
        setDepositMessage(null);
        try {
            if (parseFloat(contract.amount) < 100) {
                setDepositMessage("Minimum escrow amount is KSh 100");
                return;
            }
            // Updated to use contract_id
            await initiateEscrowDeposit({
                contract_id: contract.id,
                // phone_number: phone // Not sent to API as per new backend (uses profile)
            });
            setDepositMessage('prompt_sent');
            startPolling();
            await fetchEscrowStatus();
        } catch (err) {
            console.error("Deposit failed", err);
            const msg = err.response?.data?.error || "Failed to initiate M-Pesa deposit.";
            setDepositMessage(msg);
        } finally {
            setIsDepositing(false);
        }
    };

    const handleDownloadPDF = () => {
        const isFullySigned = contract.client_signature && contract.freelancer_signature;

        if (!isFullySigned) {
            const missing = !contract.client_signature ? 'Client' : 'Freelancer';
            alert(`This contract can only be downloaded when it is fully signed. Please wait for ${missing} to sign then proceed to download.`);
            console.log(`Download blocked: Contract partially signed by ${!contract.client_signature ? 'Freelancer only' : 'Client only'}.`);
            return;
        }

        const element = document.getElementById('printable-contract');
        const opt = {
            margin: 1,
            filename: `GigWay_Contract_${projectId.slice(0, 8)}.pdf`,
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 2, useCORS: true, letterRendering: true },
            jsPDF: { unit: 'in', format: 'letter', orientation: 'portrait' }
        };

        const originalStyle = element.style.cssText;
        element.style.maxHeight = 'none';
        element.style.background = '#ffffff';
        element.style.color = '#000000';
        element.style.padding = '40px';
        element.style.boxShadow = 'none';

        const title = document.createElement('h1');
        title.innerText = 'GIGWAY SERVICE AGREEMENT';
        title.style.textAlign = 'center';
        title.style.marginBottom = '20px';
        title.style.color = '#1e1b4b';
        element.prepend(title);

        html2pdf().set(opt).from(element).save().then(() => {
            element.style.cssText = originalStyle;
            title.remove();
        });
    };

    const isFreelancer = userType === 'freelancer';
    const isClient = userType === 'client';

    if (isLoading) return <div style={{ padding: '2rem', textAlign: 'center' }}><Loader2 className="animate-spin" /></div>;

    if (error) {
        return (
            <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--text-secondary)' }}>
                <AlertTriangle size={32} style={{ marginBottom: '1rem', color: '#ef4444' }} />
                <p>{error}</p>
            </div>
        );
    }

    const canDeposit = (isClient) && // Only client initiates deposit
        contract.client_signature &&
        contract.freelancer_signature &&
        contract.status === 'signed';

    const needsClientSignature = isClient && !contract.client_signature;
    const needsFreelancerSignature = isFreelancer && !contract.freelancer_signature;
    const showDepositForm = canDeposit && (!escrowStatus || escrowStatus.status === 'pending' || escrowStatus.status === 'failed') && escrowStatus?.status !== 'held';
    const showPendingMessage = canDeposit && escrowStatus?.status === 'pending';

    // If held, show success
    const isHeld = escrowStatus?.status === 'held' || contract.payment_status === 'escrowed';
    const milestones = contract.milestones || [];

    return (
        <div style={{ animation: 'fadeIn 0.3s ease-in-out' }}>
            {/* Status Header */}
            <div style={{
                background: 'rgba(255, 255, 255, 0.03)',
                padding: '1.5rem',
                borderRadius: '1rem',
                marginBottom: '1.5rem',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                border: '1px solid var(--glass-border)'
            }}>
                <div>
                    <h3 style={{ fontSize: '1.1rem', marginBottom: '0.25rem' }}>Contract Status</h3>
                    <span style={{
                        fontSize: '0.8rem',
                        fontWeight: '600',
                        padding: '0.3rem 0.8rem',
                        borderRadius: '20px',
                        background: contract.status === 'active' || isHeld ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                        color: contract.status === 'active' || isHeld ? '#10b981' : '#f59e0b',
                        border: '1px solid currentColor'
                    }}>
                        {contract.status.toUpperCase()}
                    </span>
                </div>

                <button
                    onClick={handleDownloadPDF}
                    style={{
                        background: 'rgba(99, 102, 241, 0.1)',
                        border: '1px solid #6366f1',
                        color: '#818cf8',
                        padding: '0.6rem 1.2rem',
                        borderRadius: '0.5rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        fontSize: '0.85rem',
                        cursor: 'pointer',
                        transition: 'all 0.2s ease',
                        fontWeight: '600'
                    }}
                >
                    <Download size={18} />
                    Download PDF
                </button>
            </div>

            {milestones.length > 0 && (
                <div className="milestone-schedule-panel">
                    <div className="milestone-schedule-header">
                        <div>
                            <h3>Milestone Payment Schedule</h3>
                            <p>
                                These milestones define review checkpoints for this contract. The current escrow deposit
                                flow remains unchanged and secures the contract amount before work proceeds.
                            </p>
                        </div>
                        <span>{milestones.length} milestones</span>
                    </div>
                    <div className="milestone-schedule-list">
                        {milestones.map((milestone, index) => (
                            <div className="milestone-schedule-item" key={milestone.id}>
                                <div className="milestone-order">{index + 1}</div>
                                <div>
                                    <h4>{milestone.title}</h4>
                                    <p>{milestone.description || 'No description provided.'}</p>
                                    <div className="milestone-meta">
                                        <span>KES {parseFloat(milestone.amount).toLocaleString()}</span>
                                        <span>{milestone.due_date ? new Date(milestone.due_date).toLocaleDateString() : 'Flexible due date'}</span>
                                        <span>{milestone.status.replace('_', ' ').toUpperCase()}</span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Contract Text */}
            <div
                id="printable-contract"
                style={{
                    background: 'var(--glass-bg)',
                    border: '1px solid var(--glass-border)',
                    borderRadius: '1rem',
                    padding: '2.5rem',
                    maxHeight: '600px',
                    overflowY: 'auto',
                    textAlign: 'left',
                    lineHeight: '1.8',
                    color: 'var(--text-secondary)',
                    marginBottom: '1.5rem',
                    whiteSpace: 'pre-wrap',
                    fontSize: '0.95rem',
                    fontFamily: "'Inter', sans-serif"
                }}>
                {/* ... (Contract text rendering logic preserved) ... */}
                {(() => {
                    let text = contract.contract_text;
                    const getDisplayName = (userObj) => {
                        if (!userObj) return null;
                        return userObj.company_name || userObj.email.split('@')[0].split(/[._]/).map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(' ');
                    };
                    const clientName = contract.client_signature && !contract.client_signature.includes('via Dashboard') ? contract.client_signature : (contract.client_signature ? getDisplayName(contract.project.client) : null);
                    const freelancerName = contract.freelancer_signature && !contract.freelancer_signature.includes('via Dashboard') ? contract.freelancer_signature : (contract.freelancer_signature ? getDisplayName(contract.project.freelancer) : null);

                    const renderSignature = (label, signature, signedAt) => (
                        <div key={label} style={{ marginTop: '1.5rem', borderTop: '1px dashed rgba(255,255,255,0.1)', paddingTop: '1.5rem' }}>
                            <div style={{ fontSize: '0.8rem', fontWeight: 'bold', color: 'var(--text-primary)', marginBottom: '0.5rem' }}>{label.toUpperCase()}:</div>
                            <div style={{ position: 'relative', height: '60px', display: 'flex', alignItems: 'center' }}>
                                <span style={{ color: 'var(--text-secondary)', marginRight: '0.5rem' }}>Signed:</span>
                                {signature ? <span style={{ fontFamily: "'Rochester', cursive", fontSize: '2rem', color: '#818cf8', transform: 'rotate(-1deg)' }}>{signature}</span> : <span style={{ opacity: 0.3 }}>________________________</span>}
                            </div>
                            <div style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Date: {signedAt ? new Date(signedAt).toLocaleDateString() : '__________________________'}</div>
                        </div>
                    );

                    const parts = text.split('SIGNATURES');
                    if (parts.length < 2) return text;
                    return (
                        <>
                            {parts[0]}
                            <span style={{ fontWeight: 'bold', fontSize: '1.1rem', color: 'var(--text-primary)' }}>SIGNATURES</span>
                            <div style={{ borderTop: '2px solid rgba(255,255,255,0.05)', marginTop: '1rem', paddingTop: '1rem' }}>
                                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '3rem' }}>
                                    {renderSignature('Client', clientName, contract.client_signed_at)}
                                    {renderSignature('Freelancer', freelancerName, contract.freelancer_signed_at)}
                                </div>
                            </div>
                        </>
                    );
                })()}
            </div>

            {/* Actions Section */}
            {(needsClientSignature || needsFreelancerSignature || showDepositForm || showPendingMessage) && (
                <div style={{
                    background: 'rgba(255, 255, 255, 0.05)',
                    padding: '2rem',
                    borderRadius: '1rem',
                    border: '1px solid var(--glass-border)',
                    textAlign: 'center'
                }}>
                    {needsClientSignature && (
                        <button className="btn btn-primary" onClick={handleSign} disabled={isSigning}>
                            {isSigning ? <Loader2 className="animate-spin" /> : <FileSignature />} Sign as Client
                        </button>
                    )}
                    {needsFreelancerSignature && (
                        <button className="btn btn-primary" onClick={handleSign} disabled={isSigning}>
                            {isSigning ? <Loader2 className="animate-spin" /> : <FileSignature />} Sign as Freelancer
                        </button>
                    )}

                    {showDepositForm && (
                        <form onSubmit={handleDeposit} style={{ maxWidth: '400px', margin: '0 auto' }}>
                            <h4>Deposit Funds to Escrow</h4>
                            <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '1.5rem' }}>
                                Funds will be held securely. Please confirm your M-Pesa number is correct in your profile ({phone}).
                            </p>
                            {depositMessage && depositMessage !== 'prompt_sent' && <p style={{ color: '#ef4444' }}>{depositMessage}</p>}
                            <button className="btn btn-primary" type="submit" disabled={isDepositing || !phone} style={{ width: '100%' }}>
                                {isDepositing ? <Loader2 className="animate-spin" /> : null} Deposit KES {parseFloat(contract.amount).toLocaleString()}
                            </button>
                        </form>
                    )}

                    {showPendingMessage && (
                        <div style={{ color: 'var(--text-secondary)' }}>M-Pesa prompt sent. Please check your phone.</div>
                    )}
                </div>
            )}

            {isHeld && (
                <div style={{ textAlign: 'center', color: '#10b981', padding: '1rem', marginTop: '1rem', background: 'rgba(16, 185, 129, 0.1)', borderRadius: '1rem' }}>
                    <CheckCircle size={32} style={{ marginBottom: '0.5rem' }} />
                    <p>Funds are secured in Escrow. Work can proceed.</p>
                </div>
            )}
        </div>
    );
};

export default ContractTab;
