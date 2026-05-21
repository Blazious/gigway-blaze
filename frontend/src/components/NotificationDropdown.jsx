import React, { useState, useEffect, useRef } from 'react';
import { Bell, Check, ExternalLink, Clock, Trash2, CheckCircle2 } from 'lucide-react';
import { getNotifications, markNotificationRead } from '../api';
import { useNavigate, Link } from 'react-router-dom';

const NotificationDropdown = () => {
    const [notifications, setNotifications] = useState([]);
    const [unreadCount, setUnreadCount] = useState(0);
    const [isOpen, setIsOpen] = useState(false);
    const [loading, setLoading] = useState(false);
    const dropdownRef = useRef(null);
    const navigate = useNavigate();

    const fetchNotifications = async () => {
        setLoading(true);
        try {
            const data = await getNotifications({ is_read: 'false' });
            setNotifications(data.slice(0, 5)); // Show only top 5 recent unread

            // For count, we might need a separate call or just use the length if limited
            // For now, let's assume we fetch all unread for the count
            setUnreadCount(data.length);
        } catch (err) {
            console.error('Failed to fetch notifications:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchNotifications();
        // Poll for new notifications every 60 seconds
        const interval = setInterval(fetchNotifications, 60000);
        return () => clearInterval(interval);
    }, []);

    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    const handleMarkRead = async (e, id) => {
        e.stopPropagation();
        try {
            await markNotificationRead(id);
            setNotifications(notifications.filter(n => n.id !== id));
            setUnreadCount(prev => Math.max(0, prev - 1));
        } catch (err) {
            console.error('Failed to mark notification as read:', err);
        }
    };

    const handleNotificationClick = async (notification) => {
        if (!notification.is_read) {
            await markNotificationRead(notification.id);
        }
        setIsOpen(false);
        // Logic to redirect based on notification type could go here
        // For now, just refresh/remove from list
        setNotifications(notifications.filter(n => n.id !== notification.id));
        setUnreadCount(prev => Math.max(0, prev - 1));

        // Example navigation (needs refinement based on notification content)
        if (notification.notification_type.includes('project')) {
            navigate('/dashboard/projects');
        } else if (notification.notification_type.includes('payment')) {
            navigate('/dashboard/wallet');
        } else if (notification.notification_type.includes('dispute')) {
            navigate('/dashboard/disputes');
        }
    };

    const formatTime = (dateString) => {
        const date = new Date(dateString);
        const now = new Date();
        const diffInSeconds = Math.floor((now - date) / 1000);

        if (diffInSeconds < 60) return 'Just now';
        if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
        if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
        return date.toLocaleDateString();
    };

    return (
        <div className="notification-wrapper" ref={dropdownRef}>
            <button
                className={`notification-bell ${isOpen ? 'active' : ''}`}
                onClick={() => setIsOpen(!isOpen)}
            >
                <Bell size={20} />
                {unreadCount > 0 && <span className="unread-badge">{unreadCount > 9 ? '9+' : unreadCount}</span>}
            </button>

            {isOpen && (
                <div className="notification-dropdown">
                    <div className="notification-header">
                        <h3>Notifications</h3>
                        {unreadCount > 0 && <span className="unread-text">{unreadCount} unread</span>}
                    </div>

                    <div className="notification-list">
                        {loading && notifications.length === 0 ? (
                            <div className="notification-empty">Loading...</div>
                        ) : notifications.length === 0 ? (
                            <div className="notification-empty">
                                <CheckCircle2 size={32} />
                                <p>All caught up!</p>
                            </div>
                        ) : (
                            notifications.map((n) => (
                                <div
                                    key={n.id}
                                    className={`notification-item ${n.is_read ? 'read' : 'unread'}`}
                                    onClick={() => handleNotificationClick(n)}
                                >
                                    <div className="notification-content">
                                        <h4>{n.title}</h4>
                                        <p>{n.message}</p>
                                        <div className="notification-meta">
                                            <Clock size={12} />
                                            <span>{formatTime(n.created_at)}</span>
                                        </div>
                                    </div>
                                    <button
                                        className="mark-read-btn"
                                        onClick={(e) => handleMarkRead(e, n.id)}
                                        title="Mark as read"
                                    >
                                        <Check size={14} />
                                    </button>
                                </div>
                            ))
                        )}
                    </div>

                    <div className="notification-footer">
                        <Link to="/dashboard/notifications" onClick={() => setIsOpen(false)}>
                            See all notifications <ExternalLink size={14} />
                        </Link>
                    </div>
                </div>
            )}
        </div>
    );
};

export default NotificationDropdown;
