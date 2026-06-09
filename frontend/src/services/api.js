import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
});

export const apiService = {
  // Configuration
  getConfig: () => api.get('/config'),

  // Jobs
  submitJob: (jobData) => api.post('/jobs', jobData),
  getJob: (jobId) => api.get(`/jobs/${jobId}`),
  listJobs: (limit = 50, status = null) => {
    const params = new URLSearchParams();
    params.append('limit', limit);
    if (status) params.append('status', status);
    return api.get(`/jobs?${params}`);
  },
  cancelJob: (jobId) => api.delete(`/jobs/${jobId}`),

  // Results
  getJobResults: (jobId) => api.get(`/jobs/${jobId}/results`),
  downloadFile: (jobId, filePath) => api.get(`/jobs/${jobId}/download/${filePath}`, {
    responseType: 'blob',
  }),
};

export default api;
