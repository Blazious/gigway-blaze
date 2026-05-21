import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
    ShieldCheck,
    Briefcase,
    Users,
    Banknote,
    Gavel,
    FileCheck
} from 'lucide-react';
import '../styles/LandingPage.css';
import freelancerImg from '../assets/freelancer.png';
import mpesaImg from '../assets/mpesa.png';
import ThemeToggle from '../components/ThemeToggle';

const LandingPage = () => {
    const navigate = useNavigate();

    return (
        <div className="landing-container">
            {/* Navigation */}
            <nav className="navbar">
                <div className="nav-logo">
                    <ShieldCheck size={32} style={{ marginRight: '8px' }} />
                    <span>Escrow</span>Gig
                </div>
                <div className="nav-links">
                    <ThemeToggle />
                    <button className="btn btn-outline" onClick={() => navigate('/login')}>Login</button>
                    <button className="btn btn-primary" onClick={() => navigate('/register')}>Get Started</button>
                </div>
            </nav>

            {/* Hero Section */}
            <header className="hero">
                <div className="hero-content">
                    <h1 className="hero-title animate-fade-up" style={{ animationDelay: '0.1s' }}>
                        Freelancing Reimagined with
                        <span>Trust & Security</span>
                    </h1>
                    <p className="hero-subtitle animate-fade-up" style={{ animationDelay: '0.3s' }}>
                        The safest way to work and hire in Kenya. Powered by M-Pesa Escrow,
                        AI-driven arbitration, and guaranteed payments.
                    </p>
                    <div className="hero-actions animate-fade-up" style={{ animationDelay: '0.5s' }}>
                        <button className="btn btn-primary" onClick={() => navigate('/register')}>Start Hiring / Working</button>
                        <button className="btn btn-outline" onClick={() => document.getElementById('features').scrollIntoView({ behavior: 'smooth' })}>Learn More</button>
                    </div>
                </div>
                <div className="hero-image-container">
                    <img src={freelancerImg} alt="Freelancer working" className="hero-image" />
                </div>
            </header>

            {/* M-Pesa Section */}
            <section className="mpesa-section">
                <div className="mpesa-image-container">
                    <img src={mpesaImg} alt="M-Pesa Money Transfer" className="mpesa-image" />
                </div>
                <div className="mpesa-content">
                    <h2 className="section-title" style={{ textAlign: 'left', marginBottom: '1rem' }}>Instant M-Pesa Payments</h2>
                    <p className="feature-desc" style={{ fontSize: '1.1rem' }}>
                        Experience the speed of mobile money. Funds move instantly from your phone to our
                        secure escrow vault. When the job is done, payments are released directly to your
                        M-Pesa wallet. No delays, no banks, just speed.
                    </p>
                </div>
            </section>

            {/* Features Grid */}
            <section id="features" className="features">
                <h2 className="section-title">Everything You Need</h2>
                <div className="feature-grid">

                    <div className="feature-card animate-fade-up" style={{ animationDelay: '0.1s' }}>
                        <div className="feature-icon"><Banknote /></div>
                        <h3 className="feature-title">Escrow Transactions</h3>
                        <p className="feature-desc">
                            Funds are held securely in M-Pesa Escrow. Clients deposit, freelancers work,
                            and funds are released only when everyone is happy.
                        </p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon"><Gavel /></div>
                        <h3 className="feature-title">Fair Disputes</h3>
                        <p className="feature-desc">
                            Conflict? No problem. Our AI-powered analysis and human review system
                            ensures fair outcomes for everyone.
                        </p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon"><Briefcase /></div>
                        <h3 className="feature-title">Project Management</h3>
                        <p className="feature-desc">
                            Create and track projects from start to finish. Set milestones,
                            timelines, and budgets with ease.
                        </p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon"><FileCheck /></div>
                        <h3 className="feature-title">Smart Contracts</h3>
                        <p className="feature-desc">
                            Auto-generated digital contracts that protect both parties.
                            Sign digitally and start working with confidence.
                        </p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon"><ShieldCheck /></div>
                        <h3 className="feature-title">Deliverable Tracking</h3>
                        <p className="feature-desc">
                            Submit work directly through the platform. Clients review and approve
                            deliverables before funds are moved.
                        </p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon"><Users /></div>
                        <h3 className="feature-title">Custom User Roles</h3>
                        <p className="feature-desc">
                            Whether you're a Freelancer looking for gigs or a Client
                            hiring talent, our platform adapts to your needs.
                        </p>
                    </div>

                </div>
            </section>

            {/* Footer */}
            <footer className="footer">
                <p>&copy; {new Date().getFullYear()} EscrowGig. Built for the Kenyan Gig Economy.</p>
            </footer>
        </div>
    );
};

export default LandingPage;
