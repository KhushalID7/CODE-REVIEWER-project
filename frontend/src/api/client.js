import axios from 'axios';

const API_BASE = 'http://localhost:8000';

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const analyzeCode = async (files) => {
  return api.post('/api/analyze', { files });
};

export const generateFix = async (path, code, issue) => {
  return api.post('/api/generate_fix', { path, code, issue });
};

export const applyPatch = async (files, patch) => {
  return api.post('/api/apply_patch', { files, patch });
};

export const healthCheck = async () => {
  return api.get('/health');
};