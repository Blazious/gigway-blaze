import React, { useState, useEffect } from 'react';
import {
    User, Lock, Bell, CreditCard, Shield, Trash2,
    Smartphone, Globe, Eye, EyeOff, Save, AlertCircle,
    CheckCircle2, X, ExternalLink
} from 'lucide-react';
import { updateProfile, changePassword, getNotificationPreferences, updateNotificationPreferences } from '../../api';
import '../../styles/Settings.css';

const Settings = () => {
    const [user, setUser] = useState(JSON.parse(localStorage.getItem('user') || '{}'));
    const [activeTab, setActiveTab] = useState('account');
    const [loading, setLoading] = useState(false);
    const [message, setMessage] = useState({ type: '', text: '' });

    // Account Settings
    const [accountData, setAccountData] = useState({
        phone_number: user.phone_number || '',
        user_type: user.user_type || ''
    });

    // Security Settings
    const [passwordData, setPasswordData] = useState({
        current_password: '',
        new_password: '',
        confirm_password: ''
    });
    const [showPasswords, setShowPasswords] = useState({
        current: false,
        new: false,
        confirm: false
    });

    // Notification Settings
    const [notifications, setNotifications] = useState({
        email_notifications: true,
        project_updates: true,
        payment_notifications: true,
        dispute_alerts: true
    });

    // Privacy Settings
    const [privacy, setPrivacy] = useState({
        profile_visibility: 'public',
        show_phone: false,
        show_email: true
    });

    useEffect(() => {
        // Load saved preferences from API and localStorage
        const fetchPreferences = async () => {
            try {
                const apiPrefs = await getNotificationPreferences();
                if (apiPrefs) {
                    setNotifications(apiPrefs);
                }
            } catch (err) {
                console.error('Failed to fetch notification preferences:', err);
                // Fallback to localStorage if API fails
                const savedNotifications = localStorage.getItem('notification_preferences');
                if (savedNotifications) {
                    setNotifications(JSON.parse(savedNotifications));
                }
            }
        };

        const savedPrivacy = localStorage.getItem('privacy_settings');
        if (savedPrivacy) {
            setPrivacy(JSON.parse(savedPrivacy));
        }

        fetchPreferences();
    }, []);

    const showMessage = (type, text) => {
        setMessage({ type, text });
        setTimeout(() => setMessage({ type: '', text: '' }), 5000);
    };

    const handleAccountUpdate = async (e) => {
        e.preventDefault();
        setLoading(true);
        setMessage({ type: '', text: '' });

        try {
            const formData = new FormData();
            formData.append('phone_number', accountData.phone_number);

            const updatedUser = await updateProfile(formData);
            localStorage.setItem('user', JSON.stringify(updatedUser));
            setUser(updatedUser);
            showMessage('success', 'Account settings updated successfully!');
        } catch (err) {
            showMessage('error', err.response?.data?.error || 'Failed to update account settings');
        } finally {
            setLoading(false);
        }
    };

    const handlePasswordChange = async (e) => {
        e.preventDefault();
        setLoading(true);
        setMessage({ type: '', text: '' });

        if (passwordData.new_password !== passwordData.confirm_password) {
            showMessage('error', 'New passwords do not match');
            setLoading(false);
            return;
        }

        if (passwordData.new_password.length < 8) {
            showMessage('error', 'Password must be at least 8 characters long');
            setLoading(false);
            return;
        }

        try {
            await changePassword({
                current_password: passwordData.current_password,
                new_password: passwordData.new_password
            });

            showMessage('success', 'Password changed successfully!');
            setPasswordData({ current_password: '', new_password: '', confirm_password: '' });
        } catch (err) {
            showMessage('error', err.response?.data?.error || 'Failed to change password. Please check your current password.');
        } finally {
            setLoading(false);
        }
    };

    const handleNotificationChange = async (key) => {
        const updated = { ...notifications, [key]: !notifications[key] };
        setNotifications(updated);

        try {
            await updateNotificationPreferences(updated);
            localStorage.setItem('notification_preferences', JSON.stringify(updated));
            showMessage('success', 'Notification preferences saved to your account');
        } catch (err) {
            showMessage('error', 'Failed to save preferences to server, but saved locally');
            localStorage.setItem('notification_preferences', JSON.stringify(updated));
        }
    };

    const handlePrivacyChange = (key, value) => {
        const updated = { ...privacy, [key]: value };
        setPrivacy(updated);
        localStorage.setItem('privacy_settings', JSON.stringify(updated));
        showMessage('success', 'Privacy settings updated');
    };

    const handleDeleteAccount = () => {
        const confirmed = window.confirm(
            'Are you sure you want to delete your account? This action cannot be undone. ' +
            'All your projects, contracts, and data will be permanently deleted.'
        );

        if (confirmed) {
            const doubleConfirm = window.confirm(
                'This is your last chance. Type DELETE in the next prompt to confirm.'
            );

            if (doubleConfirm) {
                // TODO: Implement account deletion API call
                showMessage('error', 'Account deletion is not yet implemented. Please contact support.');
            }
        }
    };

    const tabs = [
        { id: 'account', label: 'Account', icon: User },
        { id: 'security', label: 'Security', icon: Lock },
        { id: 'notifications', label: 'Notifications', icon: Bell },
        { id: 'privacy', label: 'Privacy', icon: Eye },
        { id: 'payment', label: 'Payment', icon: CreditCard }
    ];

    const renderAccountTab = () => (
        <div className="settings-section">
            <h3>Account Information</h3>
            {user.user_type === 'freelancer' && user.freelancer_readiness && (
                <div style={{
                    border: '1px solid var(--glass-border)',
                    background: 'var(--glass-bg)',
                    borderRadius: '0.75rem',
                    padding: '1rem',
                    marginBottom: '1rem'
                }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                        <Shield size={18} /> Readiness benchmark: {user.freelancer_readiness.score}%
                    </div>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', lineHeight: 1.5, margin: '0.5rem 0' }}>
                        GigWay checks profile completeness, contact details, verified proof links, and platform performance before clients review proposals.
                    </p>
                    {user.freelancer_readiness.next_actions?.length > 0 && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.35rem', color: 'var(--text-secondary)', fontSize: '0.86rem' }}>
                            {user.freelancer_readiness.next_actions.map(action => (
                                <span key={action}>- {action}</span>
                            ))}
                        </div>
                    )}
                </div>
            )}
            <form onSubmit={handleAccountUpdate}>
                <div className="form-group">
                    <label className="form-label">Email Address</label>
                    <input
                        type="email"
                        className="form-input"
                        value={user.email || ''}
                        disabled
                    />
                    <span className="helper-text">Email cannot be changed</span>
                </div>

                <div className="form-group">
                    <label className="form-label">
                        Phone Number <span className="required">*</span>
                    </label>
                    <input
                        type="tel"
                        className="form-input"
                        value={accountData.phone_number}
                        onChange={(e) => setAccountData({ ...accountData, phone_number: e.target.value })}
                        placeholder="254712345678"
                        required
                    />
                    <span className="helper-text">Used for M-Pesa payments. Format: 254712345678</span>
                </div>

                <div className="form-group">
                    <label className="form-label">Account Type</label>
                    <input
                        type="text"
                        className="form-input"
                        value={accountData.user_type === 'freelancer' ? 'Freelancer' : 'Client'}
                        disabled
                    />
                    <span className="helper-text">Account type cannot be changed</span>
                </div>

                <button type="submit" className="btn btn-primary" disabled={loading}>
                    {loading ? 'Saving...' : <><Save size={18} style={{ marginRight: '8px' }} /> Save Changes</>}
                </button>
            </form>
        </div>
    );

    const renderSecurityTab = () => (
        <div className="settings-section">
            <h3>Change Password</h3>
            <form onSubmit={handlePasswordChange}>
                <div className="form-group">
                    <label className="form-label">Current Password</label>
                    <div className="password-input-wrapper">
                        <input
                            type={showPasswords.current ? 'text' : 'password'}
                            className="form-input"
                            value={passwordData.current_password}
                            onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
                            required
                        />
                        <button
                            type="button"
                            className="password-toggle"
                            onClick={() => setShowPasswords({ ...showPasswords, current: !showPasswords.current })}
                        >
                            {showPasswords.current ? <EyeOff size={18} /> : <Eye size={18} />}
                        </button>
                    </div>
                </div>

                <div className="form-group">
                    <label className="form-label">New Password</label>
                    <div className="password-input-wrapper">
                        <input
                            type={showPasswords.new ? 'text' : 'password'}
                            className="form-input"
                            value={passwordData.new_password}
                            onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                            required
                            minLength={8}
                        />
                        <button
                            type="button"
                            className="password-toggle"
                            onClick={() => setShowPasswords({ ...showPasswords, new: !showPasswords.new })}
                        >
                            {showPasswords.new ? <EyeOff size={18} /> : <Eye size={18} />}
                        </button>
                    </div>
                    <span className="helper-text">Must be at least 8 characters long</span>
                </div>

                <div className="form-group">
                    <label className="form-label">Confirm New Password</label>
                    <div className="password-input-wrapper">
                        <input
                            type={showPasswords.confirm ? 'text' : 'password'}
                            className="form-input"
                            value={passwordData.confirm_password}
                            onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                            required
                            minLength={8}
                        />
                        <button
                            type="button"
                            className="password-toggle"
                            onClick={() => setShowPasswords({ ...showPasswords, confirm: !showPasswords.confirm })}
                        >
                            {showPasswords.confirm ? <EyeOff size={18} /> : <Eye size={18} />}
                        </button>
                    </div>
                </div>

                <button type="submit" className="btn btn-primary" disabled={loading}>
                    {loading ? 'Updating...' : <><Lock size={18} style={{ marginRight: '8px' }} /> Update Password</>}
                </button>
            </form>

            <div className="settings-divider"></div>

            <div className="settings-section">
                <h3>Two-Factor Authentication</h3>
                <div className="info-box">
                    <AlertCircle size={20} />
                    <p>Two-factor authentication is coming soon. This will add an extra layer of security to your account.</p>
                </div>
            </div>

            <div className="settings-divider"></div>

            <div className="settings-section danger-zone">
                <h3>Danger Zone</h3>
                <div className="danger-actions">
                    <div>
                        <h4>Delete Account</h4>
                        <p>Permanently delete your account and all associated data. This action cannot be undone.</p>
                    </div>
                    <button
                        className="btn btn-danger"
                        onClick={handleDeleteAccount}
                    >
                        <Trash2 size={18} style={{ marginRight: '8px' }} /> Delete Account
                    </button>
                </div>
            </div>
        </div>
    );

    const renderNotificationsTab = () => (
        <div className="settings-section">
            <h3>Email Notifications</h3>
            <p className="section-description">Choose what notifications you want to receive via email</p>

            <div className="settings-list">
                <div className="setting-item">
                    <div>
                        <h4>Email Notifications</h4>
                        <p>Receive all email notifications from EscrowGig</p>
                    </div>
                    <label className="toggle-switch">
                        <input
                            type="checkbox"
                            checked={notifications.email_notifications}
                            onChange={() => handleNotificationChange('email_notifications')}
                        />
                        <span className="toggle-slider"></span>
                    </label>
                </div>

                <div className="setting-item">
                    <div>
                        <h4>Project Updates</h4>
                        <p>Get notified when projects are updated, assigned, or completed</p>
                    </div>
                    <label className="toggle-switch">
                        <input
                            type="checkbox"
                            checked={notifications.project_updates}
                            onChange={() => handleNotificationChange('project_updates')}
                        />
                        <span className="toggle-slider"></span>
                    </label>
                </div>

                <div className="setting-item">
                    <div>
                        <h4>Payment Notifications</h4>
                        <p>Receive alerts for escrow deposits, releases, and payment confirmations</p>
                    </div>
                    <label className="toggle-switch">
                        <input
                            type="checkbox"
                            checked={notifications.payment_notifications}
                            onChange={() => handleNotificationChange('payment_notifications')}
                        />
                        <span className="toggle-slider"></span>
                    </label>
                </div>

                <div className="setting-item">
                    <div>
                        <h4>Dispute Alerts</h4>
                        <p>Get notified when disputes are raised or resolved</p>
                    </div>
                    <label className="toggle-switch">
                        <input
                            type="checkbox"
                            checked={notifications.dispute_alerts}
                            onChange={() => handleNotificationChange('dispute_alerts')}
                        />
                        <span className="toggle-slider"></span>
                    </label>
                </div>
            </div>
        </div>
    );

    const renderPrivacyTab = () => (
        <div className="settings-section">
            <h3>Privacy Settings</h3>
            <p className="section-description">Control who can see your information</p>

            <div className="form-group">
                <label className="form-label">Profile Visibility</label>
                <select
                    className="form-input"
                    value={privacy.profile_visibility}
                    onChange={(e) => handlePrivacyChange('profile_visibility', e.target.value)}
                >
                    <option value="public">Public - Anyone can view</option>
                    <option value="registered">Registered Users Only</option>
                    <option value="private">Private - Only you</option>
                </select>
            </div>

            <div className="settings-list">
                <div className="setting-item">
                    <div>
                        <h4>Show Email Address</h4>
                        <p>Display your email address on your public profile</p>
                    </div>
                    <label className="toggle-switch">
                        <input
                            type="checkbox"
                            checked={privacy.show_email}
                            onChange={(e) => handlePrivacyChange('show_email', e.target.checked)}
                        />
                        <span className="toggle-slider"></span>
                    </label>
                </div>

                <div className="setting-item">
                    <div>
                        <h4>Show Phone Number</h4>
                        <p>Display your phone number on your public profile</p>
                    </div>
                    <label className="toggle-switch">
                        <input
                            type="checkbox"
                            checked={privacy.show_phone}
                            onChange={(e) => handlePrivacyChange('show_phone', e.target.checked)}
                        />
                        <span className="toggle-slider"></span>
                    </label>
                </div>
            </div>
        </div>
    );

    const renderPaymentTab = () => (
        <div className="settings-section">
            <h3>Payment Settings</h3>
            <p className="section-description">Manage your payment preferences and M-Pesa information</p>

            <div className="info-box">
                <Smartphone size={20} />
                <div>
                    <h4>M-Pesa Phone Number</h4>
                    <p>Your phone number is used for all M-Pesa transactions including escrow deposits and payments.</p>
                    <p className="highlight">Current: {user.phone_number || 'Not set'}</p>
                    <p className="helper-text">Update your phone number in Account Settings</p>
                </div>
            </div>

            <div className="settings-divider"></div>

            <div className="settings-section">
                <h4>Payment Preferences</h4>
                <div className="info-box">
                    <CreditCard size={20} />
                    <p>Currently, EscrowGig only supports M-Pesa payments. Additional payment methods coming soon.</p>
                </div>
            </div>

            <div className="settings-divider"></div>

            <div className="settings-section">
                <h4>Transaction History</h4>
                <p>View your complete transaction history in the <a href="/dashboard/wallet" className="link">Wallet</a> section.</p>
            </div>
        </div>
    );

    return (
        <div className="settings-page">
            <div className="settings-header">
                <h1>Settings</h1>
                <p>Manage your account settings and preferences</p>
            </div>

            {message.text && (
                <div className={`message-box ${message.type}`}>
                    {message.type === 'success' ? <CheckCircle2 size={20} /> : <AlertCircle size={20} />}
                    <span>{message.text}</span>
                    <button onClick={() => setMessage({ type: '', text: '' })} className="close-message">
                        <X size={16} />
                    </button>
                </div>
            )}

            <div className="settings-container">
                <div className="settings-sidebar">
                    {tabs.map(tab => {
                        const Icon = tab.icon;
                        return (
                            <button
                                key={tab.id}
                                className={`settings-tab ${activeTab === tab.id ? 'active' : ''}`}
                                onClick={() => setActiveTab(tab.id)}
                            >
                                <Icon size={20} />
                                {tab.label}
                            </button>
                        );
                    })}
                </div>

                <div className="settings-content">
                    {activeTab === 'account' && renderAccountTab()}
                    {activeTab === 'security' && renderSecurityTab()}
                    {activeTab === 'notifications' && renderNotificationsTab()}
                    {activeTab === 'privacy' && renderPrivacyTab()}
                    {activeTab === 'payment' && renderPaymentTab()}
                </div>
            </div>
        </div>
    );
};

export default Settings;
