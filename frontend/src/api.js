import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

const api = axios.create({
    baseURL: API_BASE_URL,
});

export const getMediaUrl = (path) => {
    if (!path) return '';
    if (/^https?:\/\//i.test(path)) return path;

    const normalizedPath = String(path).replace(/^\/?(media\/)?/, '');

    if (API_BASE_URL.startsWith('http')) {
        const apiUrl = new URL(API_BASE_URL);
        return `${apiUrl.origin}/media/${normalizedPath}`;
    }

    return `/media/${normalizedPath}`;
};

// Add a request interceptor to attach the token if it exists
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

// Auth API calls
export const login = async (email, password) => {
    const response = await api.post('/auth/login/', { email, password });
    return response.data;
};

export const register = async (userData) => {
    const response = await api.post('/auth/register/', userData);
    return response.data;
};

export const updateProfile = async (formData) => {
    // formData can contain 'bio', 'phone_number', 'profile_picture' (file)
    const response = await api.patch('/auth/profile/', formData);
    return response.data;
};

export const getProfile = async () => {
    const response = await api.get('/auth/profile/');
    return response.data;
};

export const changePassword = async (passwordData) => {
    // passwordData should be { current_password, new_password }
    const response = await api.post('/auth/change-password/', passwordData);
    return response.data;
};

export const getProjects = async (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    const response = await api.get(`/projects/?${queryString}`);
    return response.data;
};

export const getWallet = async () => {
    const response = await api.get('/wallet/');
    return response.data;
};

export const getProject = async (projectId) => {
    const response = await api.get(`/projects/${projectId}/`);
    return response.data;
};

export const submitProjectReview = async (projectId, reviewData) => {
    const response = await api.post(`/projects/${projectId}/review/`, reviewData);
    return response.data;
};

export const getContract = async (projectId) => {
    const response = await api.get(`/projects/${projectId}/contract/`);
    return response.data;
};

// Updated: Uses contractId
export const signContract = async (contractId, signatureData) => {
    const response = await api.post(`/contract/${contractId}/sign/`, signatureData);
    return response.data;
};

export const createProject = async (projectData) => {
    const response = await api.post('/projects/', projectData);
    return response.data;
};

export const deleteProject = async (projectId) => {
    const response = await api.delete(`/projects/${projectId}/`);
    return response.data;
};

export const createProposal = async (proposalData) => {
    const response = await api.post('/proposals/', proposalData);
    return response.data;
};

export const generateProposalPrefill = async (projectId) => {
    const response = await api.post(`/projects/${projectId}/proposal-prefill/`);
    return response.data;
};

export const getProposals = async (projectId) => {
    const response = await api.get(`/proposals/?project=${projectId}`);
    return response.data;
};

export const getWorkHistory = async () => {
    const response = await api.get('/work-history/');
    return response.data;
};

export const createWorkHistory = async (entry) => {
    const response = await api.post('/work-history/', entry);
    return response.data;
};

export const updateWorkHistory = async (entryId, entry) => {
    const response = await api.patch(`/work-history/${entryId}/`, entry);
    return response.data;
};

export const deleteWorkHistory = async (entryId) => {
    const response = await api.delete(`/work-history/${entryId}/`);
    return response.data;
};

export const acceptProposal = async (proposalId) => {
    const response = await api.post(`/proposals/${proposalId}/accept/`);
    return response.data;
};

export const initiateEscrowDeposit = async (depositData) => {
    // depositData should be { contract_id, ... }
    const response = await api.post('/escrow/deposit/', depositData);
    return response.data;
};

export const getEscrowStatus = async (projectId) => {
    const response = await api.get(`/escrow/status/${projectId}/`);
    return response.data;
};

// Deliverable API calls
// Updated: Uses contractId
export const submitDeliverable = async (contractId, formData) => {
    // formData should contain: files, description...
    const response = await api.post(`/contract/${contractId}/submit-deliverable/`, formData);
    return response.data;
};

export const getDeliverables = async (projectId) => {
    const response = await api.get(`/deliverables/${projectId}/`);
    return response.data;
};

export const downloadDeliverableFile = async (deliverableId) => {
    const response = await api.get(`/deliverables/${deliverableId}/download/`, {
        responseType: 'blob'
    });
    return response;
};

// Updated: Single review endpoint
export const approveDeliverable = async (deliverableId, releaseData = {}) => {
    const payload = { action: 'approve' };
    if (releaseData.confirmationCode) payload.confirmation_code = releaseData.confirmationCode;
    if (releaseData.releaseComment) payload.release_comment = releaseData.releaseComment;
    if (releaseData.releaseExperience) payload.release_experience = releaseData.releaseExperience;
    const response = await api.post(`/deliverables/${deliverableId}/review/`, payload);
    return response.data;
};

export const rejectDeliverable = async (deliverableId, reason) => {
    const response = await api.post(`/deliverables/${deliverableId}/review/`, {
        action: 'reject',
        reason: reason
    });
    return response.data;
};

export const getLexaChatResponse = async (message, projectId = null) => {
    const response = await api.post('/lexa/chat/', { message, project_id: projectId });
    return response.data;
};

export const getSkillTestOptions = async () => {
    const response = await api.get('/lexa/skill-test/options/');
    return response.data;
};

export const startSkillTest = async (skill, level) => {
    const response = await api.post('/lexa/skill-test/start/', { skill, level });
    return response.data;
};

export const answerSkillTestQuestion = async (attemptId, selectedChoice = '', timedOut = false) => {
    const response = await api.post(`/lexa/skill-test/${attemptId}/answer/`, {
        selected_choice: selectedChoice,
        timed_out: timedOut
    });
    return response.data;
};

// Social Auth API calls
export const socialAuth = async (provider, accessToken, phoneNumber = null, extra = {}) => {
    const response = await api.post('/auth/social/', {
        provider,
        access_token: accessToken,
        phone_number: phoneNumber,
        ...extra
    });
    return response.data;
};

// Notification API calls
export const getNotificationPreferences = async () => {
    const response = await api.get('/notifications/preferences/');
    return response.data;
};

export const updateNotificationPreferences = async (preferences) => {
    const response = await api.put('/notifications/preferences/', preferences);
    return response.data;
};

export const getNotifications = async (params = {}) => {
    const queryString = new URLSearchParams(params).toString();
    const response = await api.get(`/notifications/?${queryString}`);
    return response.data;
};

export const markNotificationRead = async (notificationId) => {
    const response = await api.put(`/notifications/${notificationId}/read/`);
    return response.data;
};

export default api;
