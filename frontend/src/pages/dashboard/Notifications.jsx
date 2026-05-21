import React, { useState, useEffect } from 'react';
import {
    Bell, Search, Filter, CheckCircle2,
    Clock, Trash2, ArrowLeft, RefreshCw,
    AlertCircle, CheckSquare
} from 'lucide-react';
import { getNotifications, markNotificationRead } from '../../api';
import { useNavigate } from 'react-router-dom';
import '../../styles/Notifications.css';

const Notifications = () => {
    const [notifications, setNotifications] = useState([]);
    const [loading, setLoading] = useState(false);
    const [filter, setFilter] = useState('all'); // 'all', 'unread', 'read'
    const [searchQuery, setSearchQuery] = useState('');
    const navigate = useNavigate();

    const fetchNotifications = async () => {
        setLoading(true);
        try {
            const params = {};
            if (filter === 'unread') params.is_read = 'false';
            if (filter === 'read') params.is_read = 'true';

            const data = await getNotifications(params);
            setNotifications(data);
        } catch (err) {
            console.error('Failed to fetch notifications:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchNotifications();
    }, [filter]);

    const handleMarkRead = async (id) => {
        try {
            await markNotificationRead(id);
            setNotifications(notifications.map(n =>
                n.id === id ? { ...n, is_read: true } : n
            ));
        } catch (err) {
            console.error('Failed to mark notification as read:', err);
        }
    };

    const handleMarkAllRead = async () => {
        const unread = notifications.filter(n => !n.is_read);
        try {
            await Promise.all(unread.map(n => markNotificationRead(n.id)));
            setNotifications(notifications.map(n => ({ ...n, is_read: true })));
        } catch (err) {
            console.error('Failed to mark all as read:', err);
        }
    };

    const filteredNotifications = notifications.filter(n =>
        n.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
        n.message.toLowerCase().includes(searchQuery.toLowerCase())
    );

    const formatTime = (dateString) => {
        return new Date(dateString).toLocaleString([], {
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
    };

    return (
        <div className="notifications-page">
            <div className="notifications-container">
                <header className="notifications-header">
                    <div className="header-top">
                        <button className="back-btn" onClick={() => navigate(-1)}>
                            <ArrowLeft size={20} />
                        </button>
                        <h1>Notifications</h1>
                    </div>

                    <div className="header-actions">
                        <div className="search-bar">
                            <Search size={18} />
                            <input
                                type="text"
                                placeholder="Search notifications..."
                                value={searchQuery}
                                onChange={(e) => setSearchQuery(e.target.value)}
                            />
                        </div>

                        <div className="filter-group">
                            <button
                                className={`filter-btn ${filter === 'all' ? 'active' : ''}`}
                                onClick={() => setFilter('all')}
                            >
                                All
                            </button>
                            <button
                                className={`filter-btn ${filter === 'unread' ? 'active' : ''}`}
                                onClick={() => setFilter('unread')}
                            >
                                Unread
                            </button>
                            <button
                                className={`filter-btn ${filter === 'read' ? 'active' : ''}`}
                                onClick={() => setFilter('read')}
                            >
                                Read
                            </button>
                        </div>

                        <button className="mark-all-btn" onClick={handleMarkAllRead}>
                            <CheckSquare size={18} /> Mark all read
                        </button>
                    </div>
                </header>

                <div className="notifications-content">
                    {loading ? (
                        <div className="loading-state">
                            <RefreshCw className="spin" size={32} />
                            <p>Loading notifications...</p>
                        </div>
                    ) : filteredNotifications.length === 0 ? (
                        <div className="empty-state">
                            <div className="empty-icon">
                                <Bell size={48} />
                            </div>
                            <h3>No notifications found</h3>
                            <p>We'll notify you when something important happens.</p>
                        </div>
                    ) : (
                        <div className="notifications-list">
                            {filteredNotifications.map((n) => (
                                <div
                                    key={n.id}
                                    className={`notification-card ${n.is_read ? 'read' : 'unread'}`}
                                >
                                    <div className="card-status-dot"></div>
                                    <div className="card-content">
                                        <div className="card-header">
                                            <h3>{n.title}</h3>
                                            <span className="card-time">{formatTime(n.created_at)}</span>
                                        </div>
                                        <p>{n.message}</p>
                                        <div className="card-footer">
                                            <span className="type-tag">{n.notification_type.replace('_', ' ')}</span>
                                            {!n.is_read && (
                                                <button
                                                    className="action-btn"
                                                    onClick={() => handleMarkRead(n.id)}
                                                >
                                                    Mark as read
                                                </button>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default Notifications;
