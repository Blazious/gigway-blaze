import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Loader2, PlusCircle, Calendar, DollarSign, Layout, Trash2 } from 'lucide-react';
import { createProject } from '../../api';

const CreateProject = () => {
    const navigate = useNavigate();
    const [isLoading, setIsLoading] = useState(false);
    const [formData, setFormData] = useState({
        title: '',
        description: '',
        scope_of_work: '',
        budget: '',
        timeline: '',
        category: 'web_dev', // Default
        required_skills: [],
        required_tools: [],
        experience_level: '',
        preferred_background: '',
        payment_mode: 'project_completion',
        milestone_plan: []
    });
    const [skillInput, setSkillInput] = useState('');
    const [toolInput, setToolInput] = useState('');

    const handleChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const handlePaymentModeChange = (paymentMode) => {
        setFormData((prev) => ({
            ...prev,
            payment_mode: paymentMode,
            milestone_plan: paymentMode === 'milestone'
                ? (prev.milestone_plan.length ? prev.milestone_plan : [{ title: '', description: '', amount: '', due_date: '' }])
                : []
        }));
    };

    const handleMilestoneChange = (index, field, value) => {
        setFormData((prev) => {
            const nextMilestones = [...prev.milestone_plan];
            nextMilestones[index] = { ...nextMilestones[index], [field]: value };
            return { ...prev, milestone_plan: nextMilestones };
        });
    };

    const addMilestone = () => {
        setFormData((prev) => ({
            ...prev,
            milestone_plan: [
                ...prev.milestone_plan,
                { title: '', description: '', amount: '', due_date: '' }
            ]
        }));
    };

    const removeMilestone = (index) => {
        setFormData((prev) => ({
            ...prev,
            milestone_plan: prev.milestone_plan.filter((_, itemIndex) => itemIndex !== index)
        }));
    };

    const addListItem = (field, value, clearInput) => {
        const text = value.trim();
        if (!text) return;
        setFormData((prev) => {
            const current = prev[field] || [];
            if (current.some(item => item.toLowerCase() === text.toLowerCase())) return prev;
            return { ...prev, [field]: [...current, text] };
        });
        clearInput('');
    };

    const removeListItem = (field, value) => {
        setFormData((prev) => ({
            ...prev,
            [field]: (prev[field] || []).filter(item => item !== value)
        }));
    };

    const milestoneTotal = formData.milestone_plan.reduce((sum, item) => sum + (parseFloat(item.amount) || 0), 0);
    const budgetValue = parseFloat(formData.budget) || 0;
    const milestoneBalance = budgetValue - milestoneTotal;
    const milestonesBalanced = Math.abs(milestoneBalance) < 0.01;

    const handleSubmit = async (e) => {
        e.preventDefault();
        setIsLoading(true);
        try {
            const payload = {
                ...formData,
                milestone_plan: formData.payment_mode === 'milestone'
                    ? formData.milestone_plan.map((item, index) => ({ ...item, order: index + 1 }))
                    : []
            };
            await createProject(payload);
            navigate('/dashboard/projects'); // Redirect to my projects
        } catch (error) {
            console.error("Failed to create project", error);
            const errorDetail = error.response?.data?.milestone_plan || error.response?.data?.error;
            alert(errorDetail || "Failed to create project. Please try again.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
            <h2 className="section-title" style={{ textAlign: 'left', marginBottom: '1.5rem' }}>Post a New Project</h2>

            <form onSubmit={handleSubmit} style={{
                background: 'var(--glass-bg)',
                border: '1px solid var(--glass-border)',
                borderRadius: '1rem',
                padding: '2rem'
            }}>
                <div className="form-group">
                    <label className="form-label">Project Title</label>
                    <div className="input-group">
                        <Layout size={20} />
                        <input
                            type="text"
                            name="title"
                            className="form-input"
                            placeholder="e.g. E-commerce Website Redesign"
                            required
                            value={formData.title}
                            onChange={handleChange}
                        />
                    </div>
                </div>

                <div className="form-group">
                    <label className="form-label">Description</label>
                    <textarea
                        name="description"
                        className="form-input"
                        placeholder="Describe the project in detail..."
                        rows="5"
                        required
                        style={{ minHeight: '120px' }}
                        value={formData.description}
                        onChange={handleChange}
                    ></textarea>
                </div>

                <div className="form-group">
                    <label className="form-label">Scope of Work</label>
                    <textarea
                        name="scope_of_work"
                        className="form-input"
                        placeholder="List specific deliverables..."
                        rows="3"
                        required
                        value={formData.scope_of_work}
                        onChange={handleChange}
                    ></textarea>
                </div>

                <div className="form-group">
                    <label className="form-label">Hiring Criteria</label>
                    <div style={{
                        border: '1px solid var(--glass-border)',
                        borderRadius: '0.75rem',
                        padding: '1rem',
                        background: 'rgba(255,255,255,0.03)',
                        display: 'grid',
                        gap: '1rem'
                    }}>
                        <div>
                            <label className="form-label">Required skills</label>
                            <div style={{ display: 'flex', gap: '0.75rem' }}>
                                <input
                                    type="text"
                                    className="form-input"
                                    placeholder="e.g. React, Django, UI design"
                                    value={skillInput}
                                    onChange={(e) => setSkillInput(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter') {
                                            e.preventDefault();
                                            addListItem('required_skills', skillInput, setSkillInput);
                                        }
                                    }}
                                />
                                <button type="button" className="btn btn-outline" onClick={() => addListItem('required_skills', skillInput, setSkillInput)}>
                                    Add
                                </button>
                            </div>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.65rem' }}>
                                {formData.required_skills.map(skill => (
                                    <button
                                        type="button"
                                        key={skill}
                                        onClick={() => removeListItem('required_skills', skill)}
                                        style={{ border: '1px solid var(--glass-border)', background: 'var(--glass-bg)', color: 'var(--text-primary)', borderRadius: '999px', padding: '0.25rem 0.65rem', cursor: 'pointer' }}
                                        title="Remove skill"
                                    >
                                        {skill}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div>
                            <label className="form-label">Tools or platforms</label>
                            <div style={{ display: 'flex', gap: '0.75rem' }}>
                                <input
                                    type="text"
                                    className="form-input"
                                    placeholder="e.g. Figma, GitHub, PostgreSQL"
                                    value={toolInput}
                                    onChange={(e) => setToolInput(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter') {
                                            e.preventDefault();
                                            addListItem('required_tools', toolInput, setToolInput);
                                        }
                                    }}
                                />
                                <button type="button" className="btn btn-outline" onClick={() => addListItem('required_tools', toolInput, setToolInput)}>
                                    Add
                                </button>
                            </div>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginTop: '0.65rem' }}>
                                {formData.required_tools.map(tool => (
                                    <button
                                        type="button"
                                        key={tool}
                                        onClick={() => removeListItem('required_tools', tool)}
                                        style={{ border: '1px solid var(--glass-border)', background: 'var(--glass-bg)', color: 'var(--text-primary)', borderRadius: '999px', padding: '0.25rem 0.65rem', cursor: 'pointer' }}
                                        title="Remove tool"
                                    >
                                        {tool}
                                    </button>
                                ))}
                            </div>
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                            <div>
                                <label className="form-label">Experience level</label>
                                <select
                                    name="experience_level"
                                    className="form-input"
                                    value={formData.experience_level}
                                    onChange={handleChange}
                                >
                                    <option value="">Open to any level</option>
                                    <option value="junior">Junior</option>
                                    <option value="mid">Mid-level</option>
                                    <option value="senior">Senior</option>
                                    <option value="expert">Expert</option>
                                </select>
                            </div>
                            <div>
                                <label className="form-label">Preferred background</label>
                                <input
                                    type="text"
                                    name="preferred_background"
                                    className="form-input"
                                    placeholder="e.g. fintech, ecommerce, SaaS"
                                    value={formData.preferred_background}
                                    onChange={handleChange}
                                />
                            </div>
                        </div>
                    </div>
                </div>

                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                    <div className="form-group">
                        <label className="form-label">Budget (KES)</label>
                        <div className="input-group">
                            <DollarSign size={20} />
                            <input
                                type="number"
                                name="budget"
                                className="form-input"
                                placeholder="50000"
                                min="100"
                                required
                                value={formData.budget}
                                onChange={handleChange}
                            />
                        </div>
                    </div>

                    <div className="form-group">
                        <label className="form-label">Timeline (Deadline)</label>
                        <div className="input-group">
                            <Calendar size={20} />
                            <input
                                type="date"
                                name="timeline"
                                className="form-input"
                                required
                                value={formData.timeline}
                                onChange={handleChange}
                            />
                        </div>
                    </div>
                </div>

                <div className="form-group">
                    <label className="form-label">Payment Preference</label>
                    <div className="payment-mode-grid">
                        <button
                            type="button"
                            className={`payment-mode-card ${formData.payment_mode === 'project_completion' ? 'active' : ''}`}
                            onClick={() => handlePaymentModeChange('project_completion')}
                        >
                            <span>Pay at project completion</span>
                            <small>Use the current escrow flow. Client deposits once and releases after final approval.</small>
                        </button>
                        <button
                            type="button"
                            className={`payment-mode-card ${formData.payment_mode === 'milestone' ? 'active' : ''}`}
                            onClick={() => handlePaymentModeChange('milestone')}
                        >
                            <span>Pay by milestone</span>
                            <small>Add review checkpoints and payment portions that will appear in the contract.</small>
                        </button>
                    </div>
                </div>

                {formData.payment_mode === 'milestone' && (
                    <div className="milestone-editor">
                        <div className="milestone-editor-header">
                            <div>
                                <h3>Milestone Schedule</h3>
                                <p>Amounts must add up to the total project budget.</p>
                            </div>
                            <button type="button" className="btn btn-outline" onClick={addMilestone}>
                                <PlusCircle size={16} /> Add Milestone
                            </button>
                        </div>

                        {formData.milestone_plan.map((milestone, index) => (
                            <div className="milestone-form-card" key={`milestone-${index}`}>
                                <div className="milestone-form-title">
                                    <span>Milestone {index + 1}</span>
                                    {formData.milestone_plan.length > 1 && (
                                        <button type="button" className="project-icon-btn" onClick={() => removeMilestone(index)}>
                                            <Trash2 size={16} />
                                        </button>
                                    )}
                                </div>
                                <div style={{ display: 'grid', gridTemplateColumns: '1.5fr 1fr 1fr', gap: '1rem' }}>
                                    <input
                                        type="text"
                                        className="form-input"
                                        placeholder="Title"
                                        required
                                        value={milestone.title}
                                        onChange={(e) => handleMilestoneChange(index, 'title', e.target.value)}
                                    />
                                    <input
                                        type="number"
                                        className="form-input"
                                        placeholder="Amount"
                                        min="100"
                                        required
                                        value={milestone.amount}
                                        onChange={(e) => handleMilestoneChange(index, 'amount', e.target.value)}
                                    />
                                    <input
                                        type="date"
                                        className="form-input"
                                        value={milestone.due_date}
                                        onChange={(e) => handleMilestoneChange(index, 'due_date', e.target.value)}
                                    />
                                </div>
                                <textarea
                                    className="form-input"
                                    placeholder="What should be delivered at this milestone?"
                                    rows="2"
                                    value={milestone.description}
                                    onChange={(e) => handleMilestoneChange(index, 'description', e.target.value)}
                                    style={{ marginTop: '0.85rem' }}
                                />
                            </div>
                        ))}

                        <div className={`milestone-total ${Math.abs(milestoneBalance) < 0.01 ? 'balanced' : 'unbalanced'}`}>
                            <span>Milestones total: KES {milestoneTotal.toLocaleString()}</span>
                            <span>{Math.abs(milestoneBalance) < 0.01 ? 'Balanced' : `Remaining: KES ${milestoneBalance.toLocaleString()}`}</span>
                        </div>
                    </div>
                )}

                <button
                    type="submit"
                    className="btn btn-primary"
                    style={{ width: '100%', marginTop: '1rem' }}
                    disabled={isLoading || (formData.payment_mode === 'milestone' && !milestonesBalanced)}
                >
                    {isLoading ? <Loader2 className="animate-spin" size={20} /> : <PlusCircle size={20} />}
                    {isLoading ? 'Creating...' : 'Post Project'}
                </button>
            </form>
        </div>
    );
};

export default CreateProject;
