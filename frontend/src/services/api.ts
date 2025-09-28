import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Add request interceptor for debugging
api.interceptors.request.use(
  (config) => {
    console.log('Making request to:', config.url);
    return config;
  },
  (error) => {
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// Add response interceptor for debugging
api.interceptors.response.use(
  (response) => {
    console.log('Response received:', response.status);
    return response;
  },
  (error) => {
    console.error('Response error:', error.response?.status, error.message);
    return Promise.reject(error);
  }
);

// Template API
export const uploadTemplate = async (formData: FormData) => {
  const response = await api.post('/api/templates/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const setTemplatePlaceholders = async (templateId: string, placeholders: any[]) => {
  const response = await api.post(`/api/templates/${templateId}/placeholders`, placeholders);
  return response.data;
};

export const getTemplate = async (templateId: string) => {
  const response = await api.get(`/api/templates/${templateId}`);
  return response.data;
};

export const getTemplates = async () => {
  const response = await api.get('/api/templates');
  return response.data;
};

// Certificate API
export const generateCertificate = async (data: {
  template_id: string;
  student_name: string;
  course_name: string;
  date_str: string;
}) => {
  const response = await api.post('/api/certificates/generate', data);
  return response.data;
};

export const getCertificate = async (certificateId: string) => {
  const response = await api.get(`/api/certificates/${certificateId}`);
  return response.data;
};

export const getCertificates = async () => {
  const response = await api.get('/api/certificates');
  return response.data;
};

export const revokeCertificate = async (certificateId: string, reason: string) => {
  const response = await api.put(`/api/certificates/${certificateId}/revoke`, { reason });
  return response.data;
};

export const deleteCertificate = async (certificateId: string) => {
  const response = await api.delete(`/api/certificates/${certificateId}`);
  return response.data;
};

// Student Details API
export const getStudents = async () => {
  const response = await api.get('/api/students');
  return response.data;
};

export const updateStudentDetails = async (certificateId: string, studentData: any) => {
  const response = await api.put(`/api/students/${certificateId}`, studentData);
  return response.data;
};

export default api;
