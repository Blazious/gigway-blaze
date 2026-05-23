import React, { useState, useEffect } from 'react';
import { DollarSign, Clock, CheckCircle } from 'lucide-react';
import { getWallet } from '../../api';
import GigWayLoader from '../../components/GigWayLoader';

const Wallet = () => {
    const [walletData, setWalletData] = useState(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        fetchWallet();
    }, []);

    const fetchWallet = async () => {
        try {
            const data = await getWallet();
            setWalletData(data);
        } catch (error) {
            console.error("Failed to fetch wallet data", error);
        } finally {
            setIsLoading(false);
        }
    };

    if (isLoading) {
        return <GigWayLoader label="Loading wallet" />;
    }

    return (
        <div>
            <h2 className="section-title" style={{ textAlign: 'left', marginBottom: '1.5rem' }}>My Wallet</h2>

            {/* Stats Grid */}
            <div className="stats-grid">
                <div className="stat-card">
                    <div className="stat-header">
                        <span className="stat-title">Funds in Escrow</span>
                        <div className="stat-icon" style={{ background: 'rgba(245, 158, 11, 0.1)', color: '#f59e0b' }}>
                            <Clock size={20} />
                        </div>
                    </div>
                    <div className="stat-value">KES {parseFloat(walletData.in_escrow).toLocaleString()}</div>
                    <div className="stat-trend" style={{ color: '#f59e0b' }}>Held Securely</div>
                </div>

                <div className="stat-card">
                    <div className="stat-header">
                        <span className="stat-title">Total Earnings</span>
                        <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.1)', color: '#10b981' }}>
                            <DollarSign size={20} />
                        </div>
                    </div>
                    <div className="stat-value">KES {parseFloat(walletData.total_earnings).toLocaleString()}</div>
                    <div className="stat-trend">Released to M-Pesa</div>
                </div>
            </div>

            {/* Transactions Table */}
            <div className="recent-section wallet-history-section">
                <div className="wallet-history-header">
                    <h3 className="section-title" style={{ fontSize: '1.25rem', textAlign: 'left' }}>Transaction History</h3>
                    <span className="wallet-history-count">{walletData.transactions.length} records</span>
                </div>

                {walletData.transactions.length === 0 ? (
                    <div className="empty-state">
                        <p>No transactions found.</p>
                    </div>
                ) : (
                    <div className="wallet-table-scroll" role="region" aria-label="Transaction history">
                        <table className="wallet-table">
                            <thead>
                                <tr>
                                    <th>Project</th>
                                    <th>Date</th>
                                    <th>Amount</th>
                                    <th>Receipt</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {walletData.transactions.map((tx) => (
                                    <tr key={tx.id}>
                                        <td className="wallet-project-cell">{tx.project_title}</td>
                                        <td>{new Date(tx.date).toLocaleDateString()}</td>
                                        <td>KES {parseFloat(tx.amount).toLocaleString()}</td>
                                        <td>{tx.receipt || '-'}</td>
                                        <td>
                                            <span className={`wallet-status ${tx.status === 'released' ? 'released' : 'pending'}`}>
                                                {tx.status.toUpperCase()}
                                            </span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Wallet;
