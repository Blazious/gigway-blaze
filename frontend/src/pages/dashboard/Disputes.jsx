import React, { useState, useEffect, useRef } from 'react';
import { Loader2, MessageSquare, AlertTriangle, Send, Bot, User, ChevronRight, Gavel, FileText } from 'lucide-react';
import { getProjects, getLexaChatResponse } from '../../api';
import GigWayLoader from '../../components/GigWayLoader';

const Disputes = () => {
    const [projects, setProjects] = useState([]);
    const [selectedProject, setSelectedProject] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    const [messages, setMessages] = useState([
        { id: 1, text: "Welcome to the Dispute Resolution Center. I'm Lexa, your AI mediator. If you're having issues with a project, select it from the left and we can discuss the best way to move forward.", sender: 'bot' }
    ]);
    const [input, setInput] = useState('');
    const [isThinking, setIsThinking] = useState(false);
    const messagesEndRef = useRef(null);

    const user = JSON.parse(localStorage.getItem('user') || '{}');

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(() => {
        scrollToBottom();
    }, [messages, isThinking]);

    useEffect(() => {
        fetchProjects();
    }, []);

    const fetchProjects = async () => {
        try {
            // Fetch projects where I am assigned (freelancer) or owner (client)
            const data = await getProjects();
            // Filter projects that are either assigned or in progress (where disputes usually happen)
            setProjects(data.filter(p => p.status !== 'open'));
        } catch (error) {
            console.error("Failed to fetch projects", error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSend = async (e) => {
        e.preventDefault();
        if (!input.trim() || isThinking) return;

        const userMsg = { id: Date.now(), text: input, sender: 'user' };
        setMessages(prev => [...prev, userMsg]);
        setInput('');
        setIsThinking(true);

        try {
            const response = await getLexaChatResponse(input, selectedProject?.id);
            const botMsg = { id: Date.now() + 1, text: response.reply, sender: 'bot' };
            setMessages(prev => [...prev, botMsg]);
        } catch (error) {
            setMessages(prev => [...prev, {
                id: Date.now() + 1,
                text: "I'm having trouble connecting to my central processor. Please ensure your API key is configured correctly.",
                sender: 'bot',
                isError: true
            }]);
        } finally {
            setIsThinking(false);
        }
    };

    if (isLoading) return <GigWayLoader label="Loading dispute workspace" />;

    return (
        <div style={{ display: 'grid', gridTemplateColumns: '350px 1fr', gap: '2rem', height: 'calc(100vh - 200px)', animation: 'fadeIn 0.5s ease-out' }}>
            {/* Sidebar: Project Selection */}
            <div style={{
                background: 'var(--glass-bg)',
                border: '1px solid var(--glass-border)',
                borderRadius: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden'
            }}>
                <div style={{ padding: '1.5rem', borderBottom: '1px solid var(--glass-border)' }}>
                    <h3 style={{ fontSize: '1.1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <Gavel size={20} color="var(--primary)" />
                        Active Projects
                    </h3>
                </div>
                <div style={{ flex: 1, overflowY: 'auto', padding: '1rem' }}>
                    {projects.length === 0 ? (
                        <p style={{ textAlign: 'center', color: 'var(--text-secondary)', padding: '2rem' }}>No active projects found.</p>
                    ) : (
                        projects.map(project => (
                            <button
                                key={project.id}
                                onClick={() => setSelectedProject(project)}
                                style={{
                                    width: '100%',
                                    textAlign: 'left',
                                    padding: '1rem',
                                    borderRadius: '1rem',
                                    background: selectedProject?.id === project.id ? 'rgba(99, 102, 241, 0.1)' : 'transparent',
                                    border: selectedProject?.id === project.id ? '1px solid var(--primary)' : '1px solid transparent',
                                    marginBottom: '0.5rem',
                                    cursor: 'pointer',
                                    transition: 'all 0.2s',
                                    color: 'inherit'
                                }}
                            >
                                <div style={{ fontWeight: 'bold', fontSize: '0.9rem', marginBottom: '0.25rem' }}>{project.title}</div>
                                <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', display: 'flex', justifyContent: 'space-between' }}>
                                    <span>{project.status.replace('_', ' ')}</span>
                                    <span>KES {parseFloat(project.budget).toLocaleString()}</span>
                                </div>
                            </button>
                        ))
                    )}
                </div>
            </div>

            {/* Chat Area */}
            <div style={{
                background: 'var(--glass-bg)',
                border: '1px solid var(--glass-border)',
                borderRadius: '1.5rem',
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden',
                position: 'relative'
            }}>
                {/* Chat Header */}
                <div style={{
                    padding: '1.25rem 2rem',
                    borderBottom: '1px solid var(--glass-border)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '1rem',
                    background: 'rgba(255,255,255,0.02)'
                }}>
                    <div style={{
                        width: '40px',
                        height: '40px',
                        borderRadius: '50%',
                        background: 'linear-gradient(135deg, var(--primary), var(--secondary))',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        color: 'white'
                    }}>
                        <Bot size={24} />
                    </div>
                    <div>
                        <h3 style={{ margin: 0, fontSize: '1rem' }}>Lexa AI Dispute Resolver</h3>
                        <p style={{ margin: 0, fontSize: '0.75rem', color: '#10b981' }}>
                            {selectedProject ? `Discussing: ${selectedProject.title}` : 'Direct Assistance'}
                        </p>
                    </div>
                </div>

                {/* Messages Panel */}
                <div style={{ flex: 1, padding: '2rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
                    {messages.map(msg => (
                        <div key={msg.id} style={{
                            display: 'flex',
                            gap: '1rem',
                            flexDirection: msg.sender === 'bot' ? 'row' : 'row-reverse',
                            maxWidth: '80%',
                            alignSelf: msg.sender === 'bot' ? 'flex-start' : 'flex-end'
                        }}>
                            <div style={{
                                width: '32px',
                                height: '32px',
                                borderRadius: '50%',
                                background: msg.sender === 'bot' ? 'rgba(99, 102, 241, 0.1)' : 'rgba(255,255,255,0.1)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                flexShrink: 0
                            }}>
                                {msg.sender === 'bot' ? <Bot size={18} color="var(--primary)" /> : <User size={18} color="var(--text-secondary)" />}
                            </div>
                            <div style={{
                                padding: '1rem 1.25rem',
                                borderRadius: '1.25rem',
                                background: msg.sender === 'bot' ? 'rgba(255,255,255,0.05)' : 'var(--primary)',
                                color: msg.sender === 'bot' ? 'var(--text-primary)' : 'white',
                                fontSize: '0.95rem',
                                lineHeight: '1.6',
                                border: msg.sender === 'bot' ? '1px solid var(--glass-border)' : 'none',
                                borderTopLeftRadius: msg.sender === 'bot' ? '0' : '1.25rem',
                                borderTopRightRadius: msg.sender === 'user' ? '0' : '1.25rem',
                                whiteSpace: 'pre-wrap'
                            }}>
                                {msg.text}
                            </div>
                        </div>
                    ))}
                    {isThinking && (
                        <div style={{ alignSelf: 'flex-start', marginLeft: '3rem' }}>
                            <Loader2 className="animate-spin" size={20} color="var(--text-secondary)" />
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>

                {/* Input Area */}
                <form onSubmit={handleSend} style={{ padding: '1.5rem 2rem', background: 'rgba(0,0,0,0.2)', borderTop: '1px solid var(--glass-border)' }}>
                    <div style={{ position: 'relative', display: 'flex', gap: '1rem' }}>
                        <input
                            type="text"
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            placeholder={selectedProject ? `Discuss issues with "${selectedProject.title}"...` : "Choose a project to start analysis..."}
                            style={{
                                flex: 1,
                                background: 'rgba(255,255,255,0.05)',
                                border: '1px solid var(--glass-border)',
                                borderRadius: '1rem',
                                padding: '1rem 3.5rem 1rem 1.5rem',
                                color: 'white',
                                outline: 'none',
                                fontSize: '1rem'
                            }}
                            disabled={!selectedProject && messages.length > 2}
                        />
                        <button
                            type="submit"
                            style={{
                                position: 'absolute',
                                right: '0.5rem',
                                top: '0.5rem',
                                bottom: '0.5rem',
                                width: '40px',
                                background: 'var(--primary)',
                                border: 'none',
                                borderRadius: '0.75rem',
                                color: 'white',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                transition: 'transform 0.2s'
                            }}
                            onMouseOver={e => e.currentTarget.style.transform = 'scale(1.05)'}
                            onMouseOut={e => e.currentTarget.style.transform = 'scale(1)'}
                            disabled={!input.trim() || isThinking}
                        >
                            <Send size={20} />
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};

export default Disputes;
