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
    
    // Create filename
    const cleanName = studentName.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_]/g, '');
    const timestamp = new Date().toISOString().slice(0, 10);
    const filename = `${cleanName}_${timestamp}.png`;
    
    console.log(`📁 Filename: ${filename}`);
    
    // Method 1: Force download with aggressive link click
    try {
      console.log(`🔄 Method 1: Aggressive link download...`);
      
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      link.style.display = 'none';
      link.setAttribute('target', '_self');
      link.setAttribute('rel', 'noopener noreferrer');
      
      // Add event listeners to prevent default behavior
      link.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
        console.log(`🔗 Link clicked for download: ${filename}`);
      });
      
      document.body.appendChild(link);
      
      // Simulate user click
      const clickEvent = new MouseEvent('click', {
        view: window,
        bubbles: true,
        cancelable: true
      });
      
      link.dispatchEvent(clickEvent);
      
      // Clean up
      setTimeout(() => {
        if (document.body.contains(link)) {
          document.body.removeChild(link);
        }
      }, 1000);
      
      console.log(`✅ Method 1 (aggressive link) successful: ${filename}`);
      return;
      
    } catch (error) {
      console.error(`❌ Method 1 failed: ${error}`);
    }
    
    // Method 2: Hidden iframe approach
    try {
      console.log(`🔄 Method 2: Hidden iframe download...`);
      
      const iframe = document.createElement('iframe');
      iframe.style.display = 'none';
      iframe.style.width = '0';
      iframe.style.height = '0';
      iframe.style.position = 'absolute';
      iframe.style.left = '-9999px';
      iframe.style.top = '-9999px';
      iframe.src = downloadUrl;
      
      document.body.appendChild(iframe);
      
      // Remove iframe after a short delay
      setTimeout(() => {
        if (document.body.contains(iframe)) {
          document.body.removeChild(iframe);
        }
      }, 5000);
      
      console.log(`✅ Method 2 (iframe) successful: ${filename}`);
      return;
      
    } catch (error) {
      console.error(`❌ Method 2 failed: ${error}`);
    }
    
    // Method 3: Window.open with immediate close
    try {
      console.log(`🔄 Method 3: Window.open download...`);
      
      const newWindow = window.open(downloadUrl, '_blank', 'noopener,noreferrer');
      
      if (newWindow) {
        // Try to close the window immediately
        setTimeout(() => {
          try {
            newWindow.close();
          } catch (e) {
            console.log('Could not close window, user may have blocked popups');
          }
        }, 1000);
        
        console.log(`✅ Method 3 (window.open) successful: ${filename}`);
        return;
      }
      
    } catch (error) {
      console.error(`❌ Method 3 failed: ${error}`);
    }
    
    // Method 4: Form submission
    try {
      console.log(`🔄 Method 4: Form submission download...`);
      
      const form = document.createElement('form');
      form.method = 'GET';
      form.action = downloadUrl;
      form.target = '_self';
      form.style.display = 'none';
      
      document.body.appendChild(form);
      form.submit();
      
      setTimeout(() => {
        if (document.body.contains(form)) {
          document.body.removeChild(form);
        }
      }, 1000);
      
      console.log(`✅ Method 4 (form) successful: ${filename}`);
      return;
      
    } catch (error) {
      console.error(`❌ Method 4 failed: ${error}`);
    }
    
    // Method 5: Direct link (final fallback)
    try {
      console.log(`🔄 Method 5: Direct link download...`);
      
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      link.style.display = 'none';
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      console.log(`✅ Method 5 (direct link) successful: ${filename}`);
      return;
      
    } catch (error) {
      console.error(`❌ Method 5 failed: ${error}`);
    }
    
    throw new Error('All download methods failed');
    
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
