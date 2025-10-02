import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'https://certificate-tb.onrender.com';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 300000, // 5 minutes timeout for bulk operations
  withCredentials: true, // Enable credentials for CORS
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
    timeout: 60000, // 60 seconds timeout for template upload
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
  // Add cache-busting parameter to prevent caching
  const timestamp = new Date().getTime();
  const response = await api.get(`/api/templates?t=${timestamp}`);
  return response.data;
};

// Certificate API
export const generateCertificate = async (data: {
  template_id: string;
  student_name: string;
  course_name: string;
  date_str: string;
}) => {
  const response = await api.post('/api/certificates/generate', data, {
    timeout: 60000, // 60 seconds timeout for certificate generation
  });
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

export const downloadCertificateDirect = async (imageUrl: string, studentName: string): Promise<void> => {
  try {
    console.log(`🔗 Image URL: ${imageUrl}`);
    console.log(`👤 Student Name: ${studentName}`);
    
    // Convert Google Drive URL to direct download URL
    let downloadUrl = imageUrl;
    
    if (imageUrl.includes('drive.google.com/thumbnail')) {
      // Convert thumbnail URL to direct download URL
      const fileIdMatch = imageUrl.match(/[?&]id=([^&]+)/);
      if (fileIdMatch) {
        const fileId = fileIdMatch[1];
        downloadUrl = `https://drive.google.com/uc?id=${fileId}&export=download`;
        console.log(`🔄 Converted thumbnail URL to download URL: ${downloadUrl}`);
      }
    } else if (imageUrl.includes('lh3.googleusercontent.com')) {
      // Convert Google Drive sharing URL to direct download URL
      const fileIdMatch = imageUrl.match(/\/d\/([^\/]+)/);
      if (fileIdMatch) {
        const fileId = fileIdMatch[1];
        downloadUrl = `https://drive.google.com/uc?id=${fileId}&export=download`;
        console.log(`🔄 Converted sharing URL to download URL: ${downloadUrl}`);
      }
    }
    
    // Fetch the image as blob
    console.log(`📥 Fetching image from: ${downloadUrl}`);
    const response = await fetch(downloadUrl, {
      mode: 'cors',
      credentials: 'omit'
    });
    
    if (!response.ok) {
      throw new Error(`Failed to fetch image: ${response.status} ${response.statusText}`);
    }
    
    const blob = await response.blob();
    console.log(`📦 Image blob size: ${blob.size} bytes`);
    
    // Create filename
    const cleanName = studentName.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_]/g, '');
    const timestamp = new Date().toISOString().slice(0, 10);
    const filename = `${cleanName}_${timestamp}.png`;
    
    // Create download link
    const blobUrl = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = filename;
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Clean up blob URL
    setTimeout(() => URL.revokeObjectURL(blobUrl), 1000);
    
    console.log(`✅ Direct download completed: ${filename}`);
  } catch (error) {
    console.error(`❌ Direct download failed: ${error}`);
    throw error;
  }
};

// Student Details API
export const getStudents = async () => {
  const response = await api.get('/api/students');
  return response.data;
};

// Bulk Certificate Generation API
export const bulkGenerateCertificates = async (templateId: string, csvFile: File, deviceType: string = 'desktop') => {
  const formData = new FormData();
  formData.append('template_id', templateId);
  formData.append('csv_file', csvFile);
  formData.append('device_type', deviceType);
  
  // Create a separate axios instance for bulk operations with longer timeout
  const bulkApi = axios.create({
    baseURL: API_BASE_URL,
    timeout: 600000, // 10 minutes timeout for bulk operations
    withCredentials: true,
  });
  
  const response = await bulkApi.post('/api/certificates/bulk-generate', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const updateStudentDetails = async (certificateId: string, studentData: any) => {
  const response = await api.put(`/api/students/${certificateId}`, studentData);
  return response.data;
};

export default api;
