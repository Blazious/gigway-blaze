import React, { useState } from 'react';
import { X, Upload, User, Save } from 'lucide-react';
import { updateProfile } from '../api';
import '../styles/Dashboard.css'; // Reusing dashboard styles for modal

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

const ProfileModal = ({ isOpen, onClose, user, onUpdate }) => {
    const [formData, setFormData] = useState({
        bio: user.bio || '',
        phone_number: user.phone_number || '',
        profession: user.profession || '',
        skills: user.skills ? user.skills.join(', ') : '',
        country: user.country || '',
        city: user.city || '',
        company_name: user.company_name || '',
        social_links: user.social_links || { linkedin: '', twitter: '', github: '', portfolio: '', website: '' }
    });
    const [profilePic, setProfilePic] = useState(null);
    const [previewUrl, setPreviewUrl] = useState(user.profile_picture || null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');

    if (!isOpen) return null;

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handleSocialChange = (e) => {
        setFormData({
            ...formData,
            social_links: {
                ...formData.social_links,
                [e.target.name]: e.target.value
            }
        });
    };

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (file) {
            setProfilePic(file);
            setPreviewUrl(URL.createObjectURL(file));
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError('');

        const data = new FormData();
        data.append('bio', formData.bio);
        data.append('phone_number', formData.phone_number);
        data.append('profession', formData.profession);

        // Handle skills (split by comma if string)
        const skillsArray = formData.skills.split(',').map(s => s.trim()).filter(Boolean);
        data.append('skills', JSON.stringify(skillsArray));

        data.append('country', formData.country);
        data.append('city', formData.city);
        data.append('company_name', formData.company_name);
        data.append('social_links', JSON.stringify(formData.social_links));

        if (profilePic) {
            data.append('profile_picture', profilePic);
        }

        try {
            const updatedUser = await updateProfile(data);
            localStorage.setItem('user', JSON.stringify(updatedUser));
            onUpdate(updatedUser);
            onClose();
        } catch (err) {
            console.error(err);
            setError(getErrorMessage(err.response?.data) || 'Failed to update profile. Please try again.');
        } finally {
            setLoading(false);
        }
    };

    const isFreelancer = user.user_type === 'freelancer';

    return (
        <div className="modal-overlay">
            <div className="modal-content animate-fade-up">
                <div className="modal-header">
                    <h2>Edit Profile</h2>
                    <button onClick={onClose} className="close-btn">
                        <X size={24} />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="profile-form">
                    {error && <div className="error-msg">{error}</div>}

                    <div className="profile-pic-section">
                        <div className="profile-preview">
                            {previewUrl ? (
                                <img src={previewUrl} alt="Profile" />
                            ) : (
                                <div className="profile-placeholder">
                                    <User size={40} />
                                </div>
                            )}
                        </div>
                        <label className="upload-btn">
                            <Upload size={16} />
                            <span>Change Picture</span>
                            <input type="file" accept="image/*" onChange={handleFileChange} hidden />
                        </label>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Email</label>
                        <input type="text" className="form-input" value={user.email} disabled />
                        <span className="helper-text">Email cannot be changed</span>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label className="form-label">Phone Number</label>
                            <input
                                type="text"
                                name="phone_number"
                                className="form-input"
                                value={formData.phone_number}
                                onChange={handleChange}
                            />
                        </div>
                        <div className="form-group">
                            <label className="form-label">{isFreelancer ? 'Profession' : 'Industry'}</label>
                            {isFreelancer ? (
                                <select name="profession" className="form-input" value={formData.profession} onChange={handleChange}>
                                    <option value="">Select Profession</option>
                                    <option value="Backend Developer">Backend Developer</option>
                                    <option value="Frontend Developer">Frontend Developer</option>
                                    <option value="Fullstack Developer">Fullstack Developer</option>
                                    <option value="Mobile Developer">Mobile Developer</option>
                                    <option value="UI/UX Designer">UI/UX Designer</option>
                                    <option value="DevOps Engineer">DevOps Engineer</option>
                                    <option value="Data Scientist">Data Scientist</option>
                                    <option value="Content Writer">Content Writer</option>
                                </select>
                            ) : (
                                <input
                                    type="text"
                                    name="profession"
                                    className="form-input"
                                    placeholder="e.g. Fintech, E-commerce"
                                    value={formData.profession}
                                    onChange={handleChange}
                                />
                            )}
                        </div>
                    </div>

                    <div className="form-row">
                        <div className="form-group">
                            <label className="form-label">Country</label>
                            <input
                                type="text"
                                name="country"
                                className="form-input"
                                value={formData.country}
                                onChange={handleChange}
                            />
                        </div>
                        <div className="form-group">
                            <label className="form-label">City</label>
                            <input
                                type="text"
                                name="city"
                                className="form-input"
                                value={formData.city}
                                onChange={handleChange}
                            />
                        </div>
                    </div>

                    {!isFreelancer && (
                        <div className="form-group">
                            <label className="form-label">Company Name</label>
                            <input
                                type="text"
                                name="company_name"
                                className="form-input"
                                value={formData.company_name}
                                onChange={handleChange}
                            />
                        </div>
                    )}

                    {isFreelancer && (
                        <div className="form-group">
                            <label className="form-label">Skills</label>
                            <input
                                type="text"
                                name="skills"
                                className="form-input"
                                placeholder="e.g. Python, React, Django (comma separated)"
                                value={formData.skills}
                                onChange={handleChange}
                            />
                        </div>
                    )}

                    <div className="form-group">
                        <label className="form-label">Social Links</label>
                        <div className="social-inputs">
                            <input
                                type="text"
                                name="linkedin"
                                className="form-input"
                                placeholder="LinkedIn URL"
                                value={formData.social_links.linkedin || ''}
                                onChange={handleSocialChange}
                            />
                            {isFreelancer ? (
                                <>
                                    <input
                                        type="text"
                                        name="github"
                                        className="form-input"
                                        placeholder="GitHub URL"
                                        value={formData.social_links.github || ''}
                                        onChange={handleSocialChange}
                                    />
                                    <input
                                        type="text"
                                        name="portfolio"
                                        className="form-input"
                                        placeholder="Portfolio URL"
                                        value={formData.social_links.portfolio || ''}
                                        onChange={handleSocialChange}
                                    />
                                </>
                            ) : (
                                <input
                                    type="text"
                                    name="website"
                                    className="form-input"
                                    placeholder="Company Website URL"
                                    value={formData.social_links.website || ''}
                                    onChange={handleSocialChange}
                                />
                            )}
                        </div>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Bio</label>
                        <textarea
                            name="bio"
                            className="form-input"
                            rows="3"
                            value={formData.bio}
                            onChange={handleChange}
                            placeholder="Tell us about yourself..."
                        />
                    </div>

                    <button type="submit" className="btn btn-primary no-margin" disabled={loading}>
                        {loading ? 'Saving...' : (
                            <>
                                <Save size={18} style={{ marginRight: '8px' }} /> Save Changes
                            </>
                        )}
                    </button>
                </form>
            </div>

            <style jsx>{`
                .modal-overlay {
                    position: fixed;
                    top: 0;
                    left: 0;
                    right: 0;
                    bottom: 0;
                    background: rgba(15, 23, 42, 0.7);
                    backdrop-filter: blur(4px);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    z-index: 1000;
                }
                .modal-content {
                    background: var(--bg-surface);
                    padding: 1.5rem;
                    border-radius: 1.5rem;
                    width: 100%;
                    max-width: 500px;
                    max-height: 90vh;
                    overflow-y: auto;
                    border: 1px solid var(--glass-border);
                    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.25);
                }
                .modal-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 1.5rem;
                }
                .modal-header h2 {
                    margin: 0;
                    font-size: 1.5rem;
                    color: var(--text-primary);
                }
                .close-btn {
                    background: none;
                    border: none;
                    color: var(--text-secondary);
                    cursor: pointer;
                    padding: 4px;
                    transition: color 0.2s;
                }
                .close-btn:hover {
                    color: var(--danger);
                }
                .profile-pic-section {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    margin-bottom: 2rem;
                }
                .profile-preview {
                    width: 100px;
                    height: 100px;
                    border-radius: 50%;
                    overflow: hidden;
                    margin-bottom: 1rem;
                    border: 3px solid var(--primary);
                    background: var(--bg-main);
                }
                .profile-preview img {
                    width: 100%;
                    height: 100%;
                    object-fit: cover;
                }
                .profile-placeholder {
                    width: 100%;
                    height: 100%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    color: var(--text-secondary);
                }
                .upload-btn {
                    display: flex;
                    align-items: center;
                    gap: 0.5rem;
                    color: var(--primary);
                    font-weight: 500;
                    cursor: pointer;
                    padding: 0.5rem 1rem;
                    border-radius: 0.5rem;
                    background: var(--primary-glow);
                    transition: background 0.2s;
                }
                .upload-btn:hover {
                    background: rgba(249, 115, 22, 0.3);
                }
                .no-margin {
                    margin: 0;
                    width: 100%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .helper-text {
                    font-size: 0.8rem;
                    color: var(--text-secondary);
                    margin-top: 0.25rem;
                    display: block;
                }
                .form-row {
                    display: flex;
                    gap: 1rem;
                }
                .form-row .form-group {
                    flex: 1;
                }
                .social-inputs {
                    display: flex;
                    flex-direction: column;
                    gap: 0.75rem;
                }
            `}</style>
        </div>
    );
};

export default ProfileModal;
