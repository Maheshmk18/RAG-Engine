import axios from 'axios';
import { getToken, removeToken } from '../utils/auth';

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      removeToken();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export const authAPI = {
  login: async (username, password) => {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);
    const response = await api.post('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return response.data;
  },
  register: async (userData) => {
    const response = await api.post('/auth/register', userData);
    return response.data;
  },
  getCurrentUser: async () => {
    const response = await api.get('/users/me');
    return response.data;
  },
};

export const documentsAPI = {
  upload: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/documents/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
    return response.data;
  },
  list: async () => {
    const response = await api.get('/documents/');
    return response.data;
  },
  get: async (id) => {
    const response = await api.get(`/documents/${id}`);
    return response.data;
  },
  delete: async (id) => {
    const response = await api.delete(`/documents/${id}`);
    return response.data;
  },
};

export const chatAPI = {
  send: async (message, sessionId = null) => {
    const response = await api.post('/chat/', {
      message,
      session_id: sessionId,
    });
    return response.data;
  },
  getSessions: async () => {
    const response = await api.get('/chat/sessions');
    return response.data;
  },
  getSession: async (sessionId) => {
    const response = await api.get(`/chat/sessions/${sessionId}`);
    return response.data;
  },
  deleteSession: async (sessionId) => {
    const response = await api.delete(`/chat/sessions/${sessionId}`);
    return response.data;
  },
};

export const usersAPI = {
  list: async () => {
    const response = await api.get('/users/');
    return response.data;
  },
  create: async (userData) => {
    const response = await api.post('/users/', userData);
    return response.data;
  },
  get: async (id) => {
    const response = await api.get(`/users/${id}`);
    return response.data;
  },
  update: async (id, userData) => {
    const response = await api.put(`/users/${id}`, userData);
    return response.data;
  },
  delete: async (id) => {
    const response = await api.delete(`/users/${id}`);
    return response.data;
  },
};

export default api;