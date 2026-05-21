import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { User, Briefcase, Loader2 } from 'lucide-react';
import { register } from '../api';
import '../styles/Auth.css';

const buildAuthError = (err, fallback) => {
    const data = err.response?.data;
    if (!data) return fallback;
    if (typeof data === 'string') return data;
    if (data.error) return data.error;
    if (data.non_field_errors?.length) return data.non_field_errors[0];

    const messages = Object.entries(data)
        .map(([field, value]) => `${field.replace('_', ' ')}: ${Array.isArray(value) ? value[0] : value}`)
        .filter(Boolean);

    return messages[0] || fallback;
};

const RegisterPage = () => {
    const navigate = useNavigate();
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState(null);

    // Form State
    const [formData, setFormData] = useState({
        email: '',
        password: '',
        confirmPassword: '',
        phone_number: '',
        user_type: 'freelancer' // default
    });

    const handleChange = (e) => {
        setFormData({
            ...formData,
            [e.target.name]: e.target.value
        });
        setError(null);
    };

    const handleRoleSelect = (role) => {
        setFormData({ ...formData, user_type: role });
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        // Basic Validation
        if (formData.password !== formData.confirmPassword) {
            setError("Passwords do not match");
            return;
        }
        if (formData.password.length < 8) {
            setError("Password must be at least 8 characters");
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            await register({
                email: formData.email,
                password: formData.password,
                phone_number: formData.phone_number,
                user_type: formData.user_type
            });

            // Redirect to login on success
            navigate('/login', { state: { message: "Account created! Please log in." } });
        } catch (err) {
            setError(buildAuthError(err, "Registration failed. Please try again."));
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="auth-container signup-page">
            <div className="auth-card">
                <h2 className="auth-title">Create Account</h2>
                <p className="auth-subtitle">Join the safest freelance community</p>

                {error && <div className="error-msg">{error}</div>}

                <form onSubmit={handleSubmit}>
                    {/* Role Selector */}
                    <div className="role-group">
                        <div
                            className={`role-option ${formData.user_type === 'freelancer' ? 'selected' : ''}`}
                            onClick={() => handleRoleSelect('freelancer')}
                        >
                            <User className="role-icon" />
                            <span className="role-label">Freelancer</span>
                        </div>
                        <div
                            className={`role-option ${formData.user_type === 'client' ? 'selected' : ''}`}
                            onClick={() => handleRoleSelect('client')}
                        >
                            <Briefcase className="role-icon" />
                            <span className="role-label">Client</span>
                        </div>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Email Address</label>
                        <input
                            type="email"
                            name="email"
                            className="form-input"
                            value={formData.email}
                            onChange={handleChange}
                            required
                            placeholder="you@example.com"
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">M-Pesa Phone Number</label>
                        <input
                            type="text"
                            name="phone_number"
                            className="form-input"
                            value={formData.phone_number}
                            onChange={handleChange}
                            required
                            placeholder="2547..."
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Password</label>
                        <input
                            type="password"
                            name="password"
                            className="form-input"
                            value={formData.password}
                            onChange={handleChange}
                            required
                            placeholder="••••••••"
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Confirm Password</label>
                        <input
                            type="password"
                            name="confirmPassword"
                            className="form-input"
                            value={formData.confirmPassword}
                            onChange={handleChange}
                            required
                            placeholder="••••••••"
                        />
                    </div>

                    <button type="submit" className="btn btn-primary auth-btn" disabled={isLoading}>
                        {isLoading ? <Loader2 className="animate-spin mx-auto" size={20} /> : "Sign Up"}
                    </button>
                </form>

                <div className="auth-footer">
                    Already have an account?
                    <Link to="/login" className="auth-link">Log In</Link>
                </div>
            </div>
        </div>
    );
};

export default RegisterPage;
