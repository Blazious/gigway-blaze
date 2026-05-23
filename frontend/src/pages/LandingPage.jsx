import React from 'react';
import { useNavigate } from 'react-router-dom';
import {
    ShieldCheck,
    Briefcase,
    Users,
    Banknote,
    Gavel,
    FileCheck,
    Wand2,
    Star,
    UploadCloud,
    PenLine,
    Wallet,
    MousePointer2
} from 'lucide-react';
import '../styles/LandingPage.css';
import freelancerImg from '../assets/freelancer.png';
import mpesaImg from '../assets/mpesa.png';
import loginBg from '../assets/login_bg.png';
import signupBg from '../assets/signup_bg.png';
import ThemeToggle from '../components/ThemeToggle';

const LandingPage = () => {
    const navigate = useNavigate();
    const heroImages = [freelancerImg, loginBg, signupBg];

    const workflowSteps = [
        { label: 'Post', icon: <Briefcase size={16} />, text: 'Client defines scope, budget, milestones, and hiring criteria.' },
        { label: 'Match', icon: <Wand2 size={16} />, text: 'Freelancers draft proposals from real work history with Gemini.' },
        { label: 'Escrow', icon: <ShieldCheck size={16} />, text: 'Contracts are signed and funds are held before work begins.' },
        { label: 'Deliver', icon: <UploadCloud size={16} />, text: 'Files, links, or text deliverables are submitted for review.' },
        { label: 'Review', icon: <Star size={16} />, text: 'Clients approve, release payment, and leave a quality review.' }
    ];

    return (
        <div className="landing-container">
            {/* Navigation */}
            <nav className="navbar">
                <div className="nav-logo">
                    <ShieldCheck size={32} style={{ marginRight: '8px' }} />
                    <span>Gig</span>Way
                </div>
                <div className="nav-links">
                    <ThemeToggle />
                    <button className="btn btn-outline" onClick={() => navigate('/login')}>Login</button>
                    <button className="btn btn-primary" onClick={() => navigate('/register')}>Get Started</button>
                </div>
            </nav>

            {/* Hero Section */}
            <header className="hero">
                <div className="hero-backdrop" aria-hidden="true">
                    {heroImages.map((image, index) => (
                        <img
                            key={image}
                            src={image}
                            alt=""
                            className="hero-backdrop-image"
                            style={{ animationDelay: `${index * 5}s` }}
                        />
                    ))}
                </div>
                <div className="hero-content">
                    <div className="hero-kicker">Secure freelance work from brief to payout</div>
                    <h1 className="hero-title animate-fade-up" style={{ animationDelay: '0.1s' }}>
                        GigWay
                    </h1>
                    <p className="hero-subtitle animate-fade-up" style={{ animationDelay: '0.3s' }}>
                        Hire, contract, escrow, deliver, approve, and review work in one flow.
                        Built for Kenyan clients and freelancers who need trust without slowing down.
                    </p>
                    <div className="hero-actions animate-fade-up" style={{ animationDelay: '0.5s' }}>
                        <button className="btn btn-primary" onClick={() => navigate('/register')}>Start Hiring / Working</button>
                        <button className="btn btn-outline hero-outline" onClick={() => document.getElementById('workflow').scrollIntoView({ behavior: 'smooth' })}>See the Flow</button>
                    </div>
                    <div className="hero-proof">
                        <span><ShieldCheck size={16} /> Escrow protected</span>
                        <span><Wand2 size={16} /> Gemini assisted</span>
                        <span><Star size={16} /> Review backed</span>
                    </div>
                </div>
            </header>

            <section id="workflow" className="workflow-section">
                <div className="workflow-copy">
                    <p className="section-kicker">Product walkthrough</p>
                    <h2 className="section-title">One clean path from job post to paid work</h2>
                    <p className="section-lead">
                        GigWay connects the full freelance workflow: structured project briefs,
                        advisory proposal scoring, signed contracts, escrow deposits, deliverable
                        review, payment release, and client feedback.
                    </p>
                </div>

                <div className="workflow-film" aria-label="Animated product workflow preview">
                    <div className="film-toolbar">
                        <span></span>
                        <span></span>
                        <span></span>
                        <strong>gigway.app/workflow</strong>
                    </div>
                    <div className="film-screen">
                        <div className="film-panel panel-post">
                            <div className="film-sidebar">
                                <span></span><span></span><span></span><span></span>
                            </div>
                            <div className="film-main">
                                <div className="film-heading">Post a New Project</div>
                                <div className="film-input wide"></div>
                                <div className="film-input"></div>
                                <div className="film-grid">
                                    <div></div><div></div><div></div>
                                </div>
                                <div className="film-button">Add hiring criteria</div>
                            </div>
                        </div>
                        <div className="film-panel panel-proposal">
                            <div className="proposal-modal">
                                <div className="film-heading">Apply with work history</div>
                                <div className="gemini-line"><Wand2 size={14} /> Draft from My Work History</div>
                                <div className="film-text-line"></div>
                                <div className="film-text-line short"></div>
                                <div className="tag-row"><span>React</span><span>Django</span><span>Figma</span></div>
                            </div>
                        </div>
                        <div className="film-panel panel-contract">
                            <div className="contract-sheet">
                                <div className="film-heading">Contract & Escrow</div>
                                <div className="signature-row"><PenLine size={16} /> Client signed</div>
                                <div className="signature-row"><PenLine size={16} /> Freelancer signed</div>
                                <div className="escrow-pill"><Wallet size={15} /> Funds held securely</div>
                            </div>
                        </div>
                        <div className="film-panel panel-deliver">
                            <div className="deliver-box">
                                <UploadCloud size={34} />
                                <div className="film-heading">Submit Deliverable</div>
                                <p>Files, Drive links, Figma links, or text reports.</p>
                            </div>
                        </div>
                        <div className="film-panel panel-review">
                            <div className="review-box">
                                <div className="film-heading">Approve & Review</div>
                                <div className="stars">★★★★★</div>
                                <div className="film-text-line"></div>
                                <div className="film-button success">Release Funds</div>
                            </div>
                        </div>
                        <MousePointer2 className="film-cursor" size={28} />
                    </div>
                </div>

                <div className="workflow-steps">
                    {workflowSteps.map((step) => (
                        <div className="workflow-step" key={step.label}>
                            <div className="workflow-step-icon">{step.icon}</div>
                            <strong>{step.label}</strong>
                            <p>{step.text}</p>
                        </div>
                    ))}
                </div>
            </section>

            {/* Features Grid */}
            <section id="features" className="features">
                <p className="section-kicker">What the platform handles</p>
                <h2 className="section-title">Built around the actual GigWay workflow</h2>
                <div className="feature-grid">

                    <div className="feature-card animate-fade-up" style={{ animationDelay: '0.1s' }}>
                        <div className="feature-icon"><Banknote /></div>
                        <h3 className="feature-title">Escrow Transactions</h3>
                        <p className="feature-desc">
                            Clients deposit funds before work begins. Freelancers can see the funds are
                            protected before submitting deliverables.
                        </p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon"><Gavel /></div>
                        <h3 className="feature-title">Fair Disputes</h3>
                        <p className="feature-desc">
                            Lexa helps analyze project context, contract terms, deliverables, and evidence
                            when a disagreement needs a structured recommendation.
                        </p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon"><Briefcase /></div>
                        <h3 className="feature-title">Project Management</h3>
                        <p className="feature-desc">
                            Clients can define scope, budget, timeline, milestones, required skills,
                            tools, experience level, and preferred background.
                        </p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon"><FileCheck /></div>
                        <h3 className="feature-title">Smart Contracts</h3>
                        <p className="feature-desc">
                            Accepted proposals become contracts with signatures, payment status,
                            milestone schedules, and clear deliverable expectations.
                        </p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon"><ShieldCheck /></div>
                        <h3 className="feature-title">Deliverable Tracking</h3>
                        <p className="feature-desc">
                            Freelancers can submit file uploads, external links, or written work.
                            Cloudinary-backed uploads keep files available after deploys.
                        </p>
                    </div>

                    <div className="feature-card">
                        <div className="feature-icon"><Star /></div>
                        <h3 className="feature-title">Reviews & Competency</h3>
                        <p className="feature-desc">
                            Client reviews feed into freelancer readiness and proposal competency,
                            helping strong work build long-term trust.
                        </p>
                    </div>

                </div>
            </section>

            <section className="mpesa-section">
                <div className="mpesa-image-container">
                    <img src={mpesaImg} alt="M-Pesa money transfer" className="mpesa-image" />
                </div>
                <div className="mpesa-content">
                    <p className="section-kicker">Payments that match local work</p>
                    <h2 className="section-title">Escrow visibility for both sides</h2>
                    <p className="feature-desc" style={{ fontSize: '1.05rem' }}>
                        Clients see what is in escrow and what has been released. Freelancers see
                        pending payment and total earnings. The wallet view is connected to real
                        contract and escrow records.
                    </p>
                </div>
            </section>

            {/* Footer */}
            <footer className="footer">
                <p>&copy; {new Date().getFullYear()} GigWay. Built for safer freelance work.</p>
            </footer>
        </div>
    );
};

export default LandingPage;
