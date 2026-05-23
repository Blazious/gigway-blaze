import React, { useState, useEffect, useRef } from 'react';
import { MessageCircle, X, Send, Bot, User, Volume2, VolumeX, Briefcase, ShieldCheck, Clock } from 'lucide-react';
import { getLexaChatResponse, getSkillTestOptions, startSkillTest, answerSkillTestQuestion, getProfile } from '../api';
import { useLocation } from 'react-router-dom';

const LexaChatbot = () => {
    const storedUser = JSON.parse(localStorage.getItem('user') || '{}');
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState([
        {
            id: 1,
            text: storedUser.user_type === 'freelancer' && storedUser.freelancer_readiness
                ? `Hi! I'm Lexa. Your freelancer readiness score is ${storedUser.freelancer_readiness.score}%. Ask me how to improve your competency score before applying.`
                : "Hi! I'm Lexa. How can I help you today?",
            sender: 'bot'
        }
    ]);
    const [input, setInput] = useState('');
    const [isThinking, setIsThinking] = useState(false);
    const [speakingMsgId, setSpeakingMsgId] = useState(null);
    const [tourState, setTourState] = useState({ active: false, step: 0 });
    const [user, setUser] = useState(storedUser);
    const [activeMode, setActiveMode] = useState('chat');
    const [testOptions, setTestOptions] = useState(null);
    const [selectedSkill, setSelectedSkill] = useState('web_development');
    const [selectedLevel, setSelectedLevel] = useState('beginner');
    const [testState, setTestState] = useState(null);
    const [testMessages, setTestMessages] = useState([
        {
            id: 'skill-intro',
            text: "Skill Test mode is optional. Pick a skill and level, then I’ll ask one timed question at a time. A strong score can boost your competency profile.",
            sender: 'bot'
        }
    ]);
    const [timeLeft, setTimeLeft] = useState(120);
    const [isTestBusy, setIsTestBusy] = useState(false);
    const messagesEndRef = useRef(null);
    const location = useLocation();

    const tourSteps = {
        freelancer: [
            { target: '#tour-sidebar', content: "Hi! I'm Lexa. This is your primary navigation center. You can access your dashboard, projects, and wallet from here.", position: 'right' },
            { target: '.stats-grid', content: "Your dashboard includes a readiness benchmark. Improve it by completing your profile, adding real proof links, and building a clean project history.", position: 'bottom' },
            { target: '#tour-find-work', content: "New to the platform? Head over to 'Find Work' to browse and apply for open gigs that match your skills.", position: 'right' },
            { target: '#tour-notifications', content: "I'll keep you posted right here! You'll get instant alerts for project milestones, new messages, and escrow payments.", position: 'left' },
            { target: '#tour-escrow', content: "This shows your funds currently held safely in escrow. Once you submit a deliverable and the client approves it, this moves to your total earnings.", position: 'bottom' },
            { target: '#tour-earnings', content: "Congratulations! These are your released funds ready for withdrawal via M-Pesa. Hard work pays off!", position: 'bottom' },
            { target: '.lexa-toggle', content: "And of course, I'm always here! If a dispute arises or you just need help navigating, just tap my icon. Ready to start?", position: 'top' }
        ],
        client: [
            { target: '#tour-sidebar', content: "Welcome! I'm Lexa. This sidebar is your dashboard for managing projects and hiring top freelancers.", position: 'right' },
            { target: '#tour-post-project', content: "Got a task? Click here to post your project details and start receiving proposals from experts.", position: 'right' },
            { target: '#tour-notifications', content: "Watch this bell! I'll notify you as soon as a freelancer submits a proposal or a milestone deliverable for your review.", position: 'left' },
            { target: '#tour-client-escrow', content: "Your security is our priority. These funds are held in escrow and are only released once you are 100% satisfied with the work.", position: 'bottom' },
            { target: '.lexa-toggle', content: "Need aid with a contract or dispute? I'm your AI assistant. Let's build something great together!", position: 'top' }
        ]
    };

    // Extract project ID if we are on a project details page
    const projectId = location.pathname.includes('/projects/') ? location.pathname.split('/projects/')[1] : null;

    // Auto-prompt tour for first-time users
    useEffect(() => {
        const token = localStorage.getItem('token');
        const hasSeenTour = localStorage.getItem('hasSeenTour');
        const isOnDashboard = location.pathname.startsWith('/dashboard');

        if (token && !hasSeenTour && isOnDashboard && !tourState.active) {
            const timer = setTimeout(() => {
                setIsOpen(true);
                setMessages(prev => [...prev, {
                    id: Date.now(),
                    text: "Welcome to EscrowGig! 👋 I noticed it's your first time here. Would you like a quick tour of your dashboard?",
                    sender: 'bot'
                }]);
                // We'll mark it as seen once they start or skip, or just after the first prompt
                localStorage.setItem('hasSeenTour', 'true');
            }, 2500); // 2.5 second delay
            return () => clearTimeout(timer);
        }
    }, [location.pathname]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, testMessages, activeMode, isOpen]);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token || user.user_type !== 'freelancer' || testOptions) return;

        getSkillTestOptions()
            .then((data) => {
                setTestOptions(data);
                if (data.skills?.[0]) setSelectedSkill(data.skills[0].value);
                if (data.levels?.[0]) setSelectedLevel(data.levels[0].value);
            })
            .catch((error) => console.log('Skill test options unavailable:', error?.message));
    }, [user.user_type, testOptions]);

    useEffect(() => {
        if (activeMode !== 'skill' || !testState?.question || testState?.is_complete) return;

        const started = new Date(testState.question.started_at).getTime();
        const limit = testState.question.time_limit_seconds || 120;
        const tick = () => {
            const elapsed = Math.floor((Date.now() - started) / 1000);
            setTimeLeft(Math.max(0, limit - elapsed));
        };
        tick();
        const interval = setInterval(tick, 1000);
        return () => clearInterval(interval);
    }, [activeMode, testState?.question?.id, testState?.question?.started_at, testState?.is_complete]);

    useEffect(() => {
        if (activeMode !== 'skill' || !testState?.question || testState?.is_complete || isTestBusy) return;
        if (timeLeft === 0) {
            submitSkillAnswer('', true);
        }
    }, [timeLeft, activeMode, testState?.question?.id, testState?.is_complete, isTestBusy]);

    const handleSpeak = (text, id) => {
        if (speakingMsgId === id) {
            window.speechSynthesis.cancel();
            setSpeakingMsgId(null);
            return;
        }

        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);

        // Try to find a nice female voice if available
        const voices = window.speechSynthesis.getVoices();
        const preferredVoice = voices.find(v => v.name.includes('Google US English') || v.name.includes('Female')) || voices[0];
        if (preferredVoice) utterance.voice = preferredVoice;

        utterance.rate = 1.0;
        utterance.pitch = 1.1;

        utterance.onend = () => setSpeakingMsgId(null);
        utterance.onerror = () => setSpeakingMsgId(null);

        setSpeakingMsgId(id);
        window.speechSynthesis.speak(utterance);
    };

    // Cleanup speech on unmount
    useEffect(() => {
        return () => window.speechSynthesis.cancel();
    }, []);

    const startTour = () => {
        setTourState({ active: true, step: 0 });
        setIsOpen(true);
        // Add a message about starting the tour
        setMessages(prev => [...prev, { id: Date.now(), text: "Starting a quick tour of your dashboard! Follow me.", sender: 'bot' }]);
    };

    const nextTourStep = () => {
        const type = user.user_type === 'client' ? 'client' : 'freelancer';
        if (tourState.step < tourSteps[type].length - 1) {
            setTourState(prev => ({ ...prev, step: prev.step + 1 }));
        } else {
            setTourState({ active: false, step: 0 });
            setMessages(prev => [...prev, { id: Date.now(), text: "Tour complete! You're all set to use EscrowGig. How else can I help?", sender: 'bot' }]);
        }
    };

    const skipTour = () => {
        setTourState({ active: false, step: 0 });
    };

    // Auto-speak and highlight tour steps
    useEffect(() => {
        if (tourState.active) {
            const type = user.user_type === 'client' ? 'client' : 'freelancer';
            const step = tourSteps[type][tourState.step];

            // Remove previous highlights
            document.querySelectorAll('.tour-highlight').forEach(el => el.classList.remove('tour-highlight'));

            if (step) {
                handleSpeak(step.content, `tour-${tourState.step}`);

                // Add new highlight
                const targetEl = document.querySelector(step.target);
                if (targetEl) {
                    targetEl.classList.add('tour-highlight');
                    targetEl.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        } else {
            // Remove all highlights when tour ends
            document.querySelectorAll('.tour-highlight').forEach(el => el.classList.remove('tour-highlight'));
        }
    }, [tourState.active, tourState.step]);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim() || isThinking) return;

        const userMsg = { id: Date.now(), text: input, sender: 'user' };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setIsThinking(true);

        try {
            const token = localStorage.getItem('token');
            if (!token) {
                // If not logged in, fallback to some basic info or prompt to login
                setMessages(prev => [...prev, { id: Date.now() + 1, text: "I'd love to help, but you need to be logged in for my full AI capabilities!", sender: 'bot' }]);
                setIsThinking(false);
                return;
            }

            const response = await getLexaChatResponse(input, projectId);
            const botMsg = { id: Date.now() + 1, text: response.reply, sender: 'bot' };
            setMessages(prev => [...prev, botMsg]);
        } catch (error) {
            console.error("Lexa Error:", error);
            const apiError = error.response?.data?.error;
            if (error.response?.status === 401) {
                localStorage.removeItem('token');
                localStorage.removeItem('user');
            }
            setMessages(prev => [...prev, {
                id: Date.now() + 1,
                text: apiError || "I'm having trouble reaching the server right now. Please refresh and try again.",
                sender: 'bot'
            }]);
        } finally {
            setIsThinking(false);
        }
    };

    const formatSeconds = (seconds) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins}:${String(secs).padStart(2, '0')}`;
    };

    const appendTestMessage = (text, sender = 'bot') => {
        setTestMessages(prev => [...prev, { id: `${Date.now()}-${Math.random()}`, text, sender }]);
    };

    const questionText = (question) => {
        if (!question) return '';
        const choices = question.choices.map(choice => `${choice.key}. ${choice.text}`).join('\n');
        return `Question ${question.number} of ${question.total}\n${question.prompt}\n\n${choices}`;
    };

    const handleStartSkillTest = async () => {
        setIsTestBusy(true);
        try {
            const data = await startSkillTest(selectedSkill, selectedLevel);
            setTestState(data);
            const skillLabel = testOptions?.skills?.find(item => item.value === selectedSkill)?.label || selectedSkill;
            const levelLabel = testOptions?.levels?.find(item => item.value === selectedLevel)?.label || selectedLevel;
            setTestMessages([
                { id: Date.now(), text: `Starting ${levelLabel} ${skillLabel}. You have 2 minutes per question. No pressure, just answer what you know.`, sender: 'bot' },
                { id: Date.now() + 1, text: questionText(data.question), sender: 'bot' }
            ]);
        } catch (error) {
            appendTestMessage(error.response?.data?.error || 'I could not start that skill test right now.');
        } finally {
            setIsTestBusy(false);
        }
    };

    const submitSkillAnswer = async (choice, timedOut = false) => {
        if (!testState?.attempt?.id || isTestBusy) return;
        setIsTestBusy(true);
        if (timedOut) {
            appendTestMessage('Time expired. Skipping this question.', 'user');
        } else {
            appendTestMessage(choice, 'user');
        }

        try {
            const data = await answerSkillTestQuestion(testState.attempt.id, choice, timedOut);
            setTestState(data);
            if (data.is_complete) {
                const score = data.attempt.score;
                const verified = data.verified_skill?.is_verified;
                appendTestMessage(
                    verified
                        ? `Assessment complete. You scored ${score}%. Nice work - this skill is now verified and will boost your competency profile.`
                        : `Assessment complete. You scored ${score}%. You need 70% to verify this skill, but this attempt is saved. You can review and try again later.`
                );
                try {
                    const updated = await getProfile();
                    localStorage.setItem('user', JSON.stringify(updated));
                    setUser(updated);
                } catch {
                    // Ignore local profile refresh issues.
                }
            } else {
                appendTestMessage(questionText(data.question));
            }
        } catch (error) {
            appendTestMessage(error.response?.data?.error || 'I could not record that answer. Please try again.');
        } finally {
            setIsTestBusy(false);
        }
    };

    return (
        <div className="lexa-container">
            {/* Floating Toggle Button */}
            {!isOpen && (
                <button className="lexa-toggle animate-fade-up" onClick={() => setIsOpen(true)}>
                    <MessageCircle size={28} />
                    <span className="lexa-badge">Lexa AI</span>
                </button>
            )}

            {/* Chat Window */}
            {isOpen && (
                <div className="lexa-window animate-fade-up">
                    <div className="lexa-header">
                        <div className="lexa-header-info">
                            <div className="lexa-avatar">
                                <Bot size={20} />
                            </div>
                            <div>
                                <h3>Lexa</h3>
                                <p>{tourState.active ? `Tour Step ${tourState.step + 1}` : 'Online Support'}</p>
                            </div>
                        </div>
                        <div style={{ display: 'flex', gap: '0.5rem' }}>
                            {!tourState.active && (
                                <button className="lexa-tour-trigger" onClick={startTour} title="Take a tour">
                                    <Briefcase size={16} />
                                </button>
                            )}
                            <button className="lexa-close" onClick={() => setIsOpen(false)}>
                                <X size={20} />
                            </button>
                        </div>
                    </div>

                    {!tourState.active && user.user_type === 'freelancer' && (
                        <div className="lexa-mode-tabs">
                            <button className={activeMode === 'chat' ? 'active' : ''} onClick={() => setActiveMode('chat')}>
                                Ask Lexa
                            </button>
                            <button className={activeMode === 'skill' ? 'active' : ''} onClick={() => setActiveMode('skill')}>
                                Skill Test
                            </button>
                        </div>
                    )}

                    <div className="lexa-messages">
                        {tourState.active ? (
                            <div className="lexa-tour-card animate-fade-up">
                                <p>{(user.user_type === 'client' ? tourSteps.client : tourSteps.freelancer)[tourState.step]?.content}</p>
                                <div className="lexa-tour-actions">
                                    <button className="btn-tour-skip" onClick={skipTour}>Skip</button>
                                    <button className="btn-tour-next" onClick={nextTourStep}>
                                        {tourState.step === (user.user_type === 'client' ? tourSteps.client : tourSteps.freelancer).length - 1 ? 'Finish' : 'Next'}
                                    </button>
                                </div>
                            </div>
                        ) : activeMode === 'skill' && user.user_type === 'freelancer' ? (
                            <>
                                {!testState?.question && !testState?.is_complete && (
                                    <div className="lexa-test-setup">
                                        <div className="lexa-test-title">
                                            <ShieldCheck size={18} />
                                            <span>Lexa Skill Verification</span>
                                        </div>
                                        <label>Skill</label>
                                        <select value={selectedSkill} onChange={(e) => setSelectedSkill(e.target.value)}>
                                            {(testOptions?.skills || []).map(skill => (
                                                <option key={skill.value} value={skill.value}>{skill.label}</option>
                                            ))}
                                        </select>
                                        <label>Level</label>
                                        <select value={selectedLevel} onChange={(e) => setSelectedLevel(e.target.value)}>
                                            {(testOptions?.levels || []).map(level => (
                                                <option key={level.value} value={level.value}>{level.label}</option>
                                            ))}
                                        </select>
                                        <button className="lexa-start-test" onClick={handleStartSkillTest} disabled={isTestBusy || !testOptions?.skills?.length}>
                                            {isTestBusy ? 'Starting...' : 'Start Test'}
                                        </button>
                                    </div>
                                )}

                                {testState?.question && !testState?.is_complete && (
                                    <div className={`lexa-timer ${timeLeft <= 20 ? 'warning' : ''}`}>
                                        <Clock size={14} /> {formatSeconds(timeLeft)}
                                    </div>
                                )}

                                {testMessages.map((msg) => (
                                    <div key={msg.id} className={`lexa-msg-wrapper ${msg.sender}`}>
                                        <div className="lexa-msg-icon">
                                            {msg.sender === 'bot' ? <Bot size={14} /> : <User size={14} />}
                                        </div>
                                        <div className="lexa-msg-bubble">{msg.text}</div>
                                    </div>
                                ))}

                                {testState?.question && !testState?.is_complete && (
                                    <div className="lexa-choice-grid">
                                        {testState.question.choices.map(choice => (
                                            <button
                                                key={choice.key}
                                                onClick={() => submitSkillAnswer(choice.key)}
                                                disabled={isTestBusy}
                                            >
                                                {choice.key}
                                            </button>
                                        ))}
                                        <button onClick={() => submitSkillAnswer('', true)} disabled={isTestBusy}>
                                            Skip
                                        </button>
                                    </div>
                                )}
                            </>
                        ) : (
                            messages.map((msg) => (
                                <div key={msg.id} className={`lexa-msg-wrapper ${msg.sender}`}>
                                    <div className="lexa-msg-icon">
                                        {msg.sender === 'bot' ? <Bot size={14} /> : <User size={14} />}
                                    </div>
                                    <div className="lexa-msg-bubble">
                                        {msg.text}
                                        {msg.sender === 'bot' && (
                                            <button
                                                className={`lexa-speak-btn ${speakingMsgId === msg.id ? 'active' : ''}`}
                                                onClick={() => handleSpeak(msg.text, msg.id)}
                                                title={speakingMsgId === msg.id ? "Stop speaking" : "Listen to response"}
                                            >
                                                {speakingMsgId === msg.id ? <VolumeX size={14} /> : <Volume2 size={14} />}
                                            </button>
                                        )}
                                    </div>
                                </div>
                            ))
                        )}
                        {isThinking && (
                            <div className="lexa-msg-wrapper bot">
                                <div className="lexa-msg-icon"><Bot size={14} /></div>
                                <div className="lexa-msg-bubble thinking">
                                    <span className="dot">.</span><span className="dot">.</span><span className="dot">.</span>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>

                    {activeMode === 'chat' || user.user_type !== 'freelancer' ? (
                        <form className="lexa-input-area" onSubmit={handleSend}>
                            <input
                                type="text"
                                placeholder="Type your question..."
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                            />
                            <button type="submit" disabled={!input.trim()}>
                                <Send size={18} />
                            </button>
                        </form>
                    ) : (
                        <div className="lexa-input-area lexa-test-footer">
                            {testState?.is_complete ? 'Skill test complete. Start another one whenever you are ready.' : 'Answer using the buttons above before time runs out.'}
                        </div>
                    )}
                </div>
            )}

            <style jsx>{`
                .lexa-container {
                    position: fixed;
                    bottom: 2rem;
                    right: 2rem;
                    z-index: 9999;
                    font-family: inherit;
                }

                .lexa-toggle {
                    width: 64px;
                    height: 64px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, var(--primary), var(--secondary));
                    color: white;
                    border: none;
                    box-shadow: 0 10px 25px var(--primary-glow);
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
                    position: relative;
                }

                .lexa-toggle:hover {
                    transform: scale(1.1);
                }

                .lexa-badge {
                    position: absolute;
                    top: -10px;
                    right: -10px;
                    background: var(--text-primary);
                    color: white;
                    font-size: 10px;
                    font-weight: 700;
                    padding: 4px 8px;
                    border-radius: 99px;
                    white-space: nowrap;
                    border: 2px solid white;
                }

                .lexa-window {
                    width: 350px;
                    height: 500px;
                    background: var(--bg-surface);
                    border-radius: 1.5rem;
                    display: flex;
                    flex-direction: column;
                    box-shadow: 0 20px 50px rgba(0,0,0,0.2);
                    border: 1px solid var(--glass-border);
                    overflow: hidden;
                    backdrop-filter: blur(10px);
                }

                .lexa-header {
                    padding: 1.25rem;
                    background: linear-gradient(to right, var(--primary), var(--secondary));
                    color: white;
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }

                .lexa-header-info {
                    display: flex;
                    align-items: center;
                    gap: 0.75rem;
                }

                .lexa-avatar {
                    width: 36px;
                    height: 36px;
                    background: rgba(255,255,255,0.2);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }

                .lexa-header h3 {
                    margin: 0;
                    font-size: 1.1rem;
                    font-weight: 700;
                }

                .lexa-header p {
                    margin: 0;
                    font-size: 0.75rem;
                    opacity: 0.8;
                }

                .lexa-close {
                    background: none;
                    border: none;
                    color: white;
                    cursor: pointer;
                    opacity: 0.7;
                    transition: opacity 0.2s;
                }

                .lexa-close:hover {
                    opacity: 1;
                }

                .lexa-mode-tabs {
                    display: grid;
                    grid-template-columns: 1fr 1fr;
                    gap: 0.35rem;
                    padding: 0.55rem;
                    background: white;
                    border-bottom: 1px solid var(--glass-border);
                }

                .lexa-mode-tabs button {
                    border: 1px solid transparent;
                    background: transparent;
                    color: var(--text-secondary);
                    border-radius: 999px;
                    padding: 0.45rem 0.6rem;
                    font-size: 0.8rem;
                    font-weight: 800;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .lexa-mode-tabs button.active {
                    background: var(--primary-glow);
                    border-color: rgba(249, 115, 22, 0.28);
                    color: var(--primary);
                }

                .lexa-messages {
                    flex: 1;
                    padding: 1.25rem;
                    overflow-y: auto;
                    display: flex;
                    flex-direction: column;
                    gap: 1rem;
                    background: #f8fafc;
                }

                .lexa-test-setup {
                    background: white;
                    border: 1px solid rgba(15, 23, 42, 0.08);
                    border-radius: 1rem;
                    padding: 1rem;
                    display: flex;
                    flex-direction: column;
                    gap: 0.65rem;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.03);
                }

                .lexa-test-title {
                    display: flex;
                    align-items: center;
                    gap: 0.45rem;
                    color: var(--primary);
                    font-weight: 800;
                    margin-bottom: 0.25rem;
                }

                .lexa-test-setup label {
                    color: var(--text-secondary);
                    font-size: 0.72rem;
                    font-weight: 800;
                    text-transform: uppercase;
                }

                .lexa-test-setup select {
                    width: 100%;
                    border: 1px solid #e2e8f0;
                    border-radius: 0.65rem;
                    padding: 0.6rem;
                    color: var(--text-primary);
                    background: white;
                    font: inherit;
                }

                .lexa-start-test {
                    border: none;
                    border-radius: 999px;
                    background: var(--primary);
                    color: white;
                    padding: 0.65rem 1rem;
                    font-weight: 800;
                    cursor: pointer;
                    margin-top: 0.25rem;
                }

                .lexa-start-test:disabled {
                    opacity: 0.55;
                    cursor: not-allowed;
                }

                .lexa-timer {
                    align-self: center;
                    display: inline-flex;
                    align-items: center;
                    gap: 0.35rem;
                    background: white;
                    border: 1px solid rgba(15, 23, 42, 0.08);
                    color: var(--text-primary);
                    border-radius: 999px;
                    padding: 0.35rem 0.75rem;
                    font-size: 0.8rem;
                    font-weight: 900;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.04);
                }

                .lexa-timer.warning {
                    color: #ef4444;
                    border-color: rgba(239, 68, 68, 0.25);
                    background: rgba(239, 68, 68, 0.08);
                }

                .lexa-choice-grid {
                    display: grid;
                    grid-template-columns: repeat(5, 1fr);
                    gap: 0.4rem;
                    background: white;
                    border: 1px solid rgba(15, 23, 42, 0.08);
                    border-radius: 1rem;
                    padding: 0.65rem;
                }

                .lexa-choice-grid button {
                    border: 1px solid #e2e8f0;
                    background: #f8fafc;
                    color: var(--text-primary);
                    border-radius: 0.7rem;
                    padding: 0.55rem 0.35rem;
                    font-weight: 900;
                    cursor: pointer;
                    transition: all 0.2s;
                }

                .lexa-choice-grid button:hover:not(:disabled) {
                    background: var(--primary);
                    color: white;
                    border-color: var(--primary);
                }

                .lexa-choice-grid button:disabled {
                    opacity: 0.55;
                    cursor: not-allowed;
                }

                .lexa-msg-wrapper {
                    display: flex;
                    gap: 0.5rem;
                    max-width: 85%;
                }

                .lexa-msg-wrapper.bot {
                    align-self: flex-start;
                }

                .lexa-msg-wrapper.user {
                    align-self: flex-end;
                    flex-direction: row-reverse;
                }

                .lexa-msg-icon {
                    width: 24px;
                    height: 24px;
                    border-radius: 50%;
                    background: white;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    flex-shrink: 0;
                    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
                }

                .bot .lexa-msg-icon { color: var(--primary); }
                .user .lexa-msg-icon { color: var(--text-secondary); }

                .lexa-msg-bubble {
                    padding: 0.75rem 1rem;
                    border-radius: 1rem;
                    font-size: 0.9rem;
                    line-height: 1.4;
                    white-space: pre-wrap;
                    position: relative;
                }

                .lexa-speak-btn {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    background: rgba(var(--primary-rgb), 0.1);
                    border: none;
                    color: var(--primary);
                    border-radius: 50%;
                    width: 24px;
                    height: 24px;
                    margin-left: 0.5rem;
                    cursor: pointer;
                    vertical-align: middle;
                    opacity: 0.6;
                    transition: all 0.2s;
                }

                .lexa-speak-btn:hover, .lexa-speak-btn.active {
                    opacity: 1;
                    background: var(--primary);
                    color: white;
                }

                .lexa-speak-btn.active {
                    animation: pulse 1.5s infinite;
                }

                @keyframes pulse {
                    0% { transform: scale(1); }
                    50% { transform: scale(1.1); }
                    100% { transform: scale(1); }
                }

                .bot .lexa-msg-bubble {
                    background: white;
                    color: var(--text-primary);
                    border-bottom-left-radius: 0;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.03);
                }

                .user .lexa-msg-bubble {
                    background: var(--primary);
                    color: white;
                    border-bottom-right-radius: 0;
                }

                .lexa-msg-bubble.thinking .dot {
                    animation: blink 1.4s infinite;
                    font-size: 1.5rem;
                    line-height: 0.5;
                }
                .lexa-msg-bubble.thinking .dot:nth-child(2) { animation-delay: 0.2s; }
                .lexa-msg-bubble.thinking .dot:nth-child(3) { animation-delay: 0.4s; }

                @keyframes blink {
                    0% { opacity: 0.2; }
                    20% { opacity: 1; }
                    100% { opacity: 0.2; }
                }

                .lexa-input-area {
                    padding: 1rem;
                    display: flex;
                    gap: 0.5rem;
                    border-top: 1px solid var(--glass-border);
                    background: white;
                }

                .lexa-test-footer {
                    color: var(--text-secondary);
                    font-size: 0.8rem;
                    justify-content: center;
                    text-align: center;
                    font-weight: 700;
                }

                .lexa-input-area input {
                    flex: 1;
                    border: 1px solid #e2e8f0;
                    border-radius: 99px;
                    padding: 0.6rem 1rem;
                    font-size: 0.9rem;
                    outline: none;
                    transition: border-color 0.2s;
                }

                .lexa-input-area input:focus {
                    border-color: var(--primary);
                }

                .lexa-input-area button {
                    width: 36px;
                    height: 36px;
                    border-radius: 50%;
                    background: var(--primary);
                    color: white;
                    border: none;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: opacity 0.2s;
                }

                .lexa-input-area button:disabled {
                    opacity: 0.5;
                    cursor: not-allowed;
                }

                .lexa-tour-trigger {
                    background: rgba(255,255,255,0.2);
                    border: none;
                    color: white;
                    width: 30px;
                    height: 30px;
                    border-radius: 50%;
                    cursor: pointer;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: background 0.2s;
                }

                .lexa-tour-trigger:hover {
                    background: rgba(255,255,255,0.4);
                }

                .lexa-tour-card {
                    background: white;
                    padding: 1.5rem;
                    border-radius: 1rem;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.05);
                    border: 1px solid var(--primary-glow);
                }

                .lexa-tour-card p {
                    font-size: 0.95rem;
                    color: var(--text-primary);
                    line-height: 1.6;
                    margin-bottom: 1.5rem;
                }

                .lexa-tour-actions {
                    display: flex;
                    justify-content: space-between;
                    gap: 1rem;
                }

                .btn-tour-skip {
                    padding: 0.5rem 1rem;
                    border: 1px solid #e2e8f0;
                    background: white;
                    color: var(--text-secondary);
                    border-radius: 99px;
                    font-size: 0.85rem;
                    cursor: pointer;
                }

                .btn-tour-next {
                    flex: 1;
                    padding: 0.5rem 1rem;
                    background: var(--primary);
                    color: white;
                    border: none;
                    border-radius: 99px;
                    font-size: 0.85rem;
                    font-weight: 600;
                    cursor: pointer;
                    box-shadow: 0 4px 10px var(--primary-glow);
                }

                /* Highlight Pulse Effect */
                .tour-highlight {
                    position: relative;
                    z-index: 10001 !important;
                    box-shadow: 0 0 0 4px var(--primary), 0 0 20px var(--primary-glow) !important;
                    border-radius: 8px !important;
                    transition: all 0.3s ease-in-out !important;
                    pointer-events: none;
                }
            `}</style>
        </div>
    );
};

export default LexaChatbot;
