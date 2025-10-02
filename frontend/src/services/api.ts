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
    
    // Detect mobile device
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    const isAndroid = /Android/.test(navigator.userAgent);
    
    console.log(`📱 Device Info: Mobile=${isMobile}, iOS=${isIOS}, Android=${isAndroid}`);
    
    // Convert Google Drive URL to direct download URL
    let downloadUrl = imageUrl;
    
    if (imageUrl.includes('drive.google.com/thumbnail')) {
      const fileIdMatch = imageUrl.match(/[?&]id=([^&]+)/);
      if (fileIdMatch) {
        const fileId = fileIdMatch[1];
        downloadUrl = `https://drive.google.com/uc?id=${fileId}&export=download`;
        console.log(`🔄 Converted to download URL: ${downloadUrl}`);
      }
    } else if (imageUrl.includes('lh3.googleusercontent.com')) {
      const fileIdMatch = imageUrl.match(/\/d\/([^\/]+)/);
      if (fileIdMatch) {
        const fileId = fileIdMatch[1];
        downloadUrl = `https://drive.google.com/uc?id=${fileId}&export=download`;
        console.log(`🔄 Converted to download URL: ${downloadUrl}`);
      }
    }
    
    // Create filename
    const cleanName = studentName.replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_]/g, '');
    const timestamp = new Date().toISOString().slice(0, 10);
    const filename = `${cleanName}_${timestamp}.png`;
    
    console.log(`📁 Student Name: ${studentName}`);
    console.log(`📁 Clean Name: ${cleanName}`);
    console.log(`📁 Timestamp: ${timestamp}`);
    console.log(`📁 Final Filename: ${filename}`);
    
    // Method 1: iOS Web Share API (best for iOS)
    if (isIOS && navigator.share) {
      try {
        console.log(`📱 Trying iOS Web Share API...`);
        
        // Fetch the image as blob first
        const response = await fetch(downloadUrl, { mode: 'cors' });
        if (response.ok) {
          const blob = await response.blob();
          const file = new File([blob], filename, { type: 'image/png' });
          
          await navigator.share({
            title: 'Certificate Download',
            text: `Certificate for ${studentName}`,
            files: [file]
          });
          
          console.log(`✅ iOS Web Share successful: ${filename}`);
          return;
        }
      } catch (error) {
        console.error(`❌ iOS Web Share failed: ${error}`);
      }
    }
    
    // Method 2: Android/Generic Mobile - Force actual download
    if (isMobile) {
      // Try blob download with proper headers (most reliable for actual file download)
      try {
        console.log(`📱 Trying mobile blob download with headers...`);
        
        const response = await fetch(downloadUrl, {
          method: 'GET',
          headers: {
            'Accept': 'image/png,image/jpeg,image/*,*/*',
            'Cache-Control': 'no-cache'
          },
          mode: 'cors'
        });
        
        if (response.ok) {
          const blob = await response.blob();
          const blobUrl = URL.createObjectURL(blob);
          
          const link = document.createElement('a');
          link.href = blobUrl;
          link.download = filename;
          link.style.display = 'none';
          
          // Add click event to force download
          link.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
          });
          
          document.body.appendChild(link);
          
          // Force click multiple times for mobile
          link.click();
          setTimeout(() => link.click(), 100);
          setTimeout(() => link.click(), 200);
          
          document.body.removeChild(link);
          
          // Clean up blob URL
          setTimeout(() => URL.revokeObjectURL(blobUrl), 5000);
          
          console.log(`✅ Mobile blob download successful: ${filename}`);
          return;
        }
      } catch (error) {
        console.error(`❌ Mobile blob download failed: ${error}`);
      }
      
      // Try direct link with forced download
      try {
        console.log(`📱 Trying mobile direct link with force...`);
        
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = filename;
        link.style.display = 'none';
        
        // Add multiple attributes to force download
        link.setAttribute('download', filename);
        link.setAttribute('target', '_self');
        link.setAttribute('rel', 'noopener noreferrer');
        
        // Add click event to prevent navigation
        link.addEventListener('click', (e) => {
          e.preventDefault();
          e.stopPropagation();
        });
        
        document.body.appendChild(link);
        
        // Force click multiple times
        link.click();
        setTimeout(() => link.click(), 100);
        setTimeout(() => link.click(), 200);
        
        document.body.removeChild(link);
        
        console.log(`✅ Mobile direct link successful: ${filename}`);
        return;
        
      } catch (error) {
        console.error(`❌ Mobile direct link failed: ${error}`);
      }
      
      // Try window.open for Android (last resort)
      if (isAndroid) {
        try {
          console.log(`🤖 Trying Android window.open...`);
          
          const newWindow = window.open(downloadUrl, '_blank', 'noopener,noreferrer');
          if (newWindow) {
            // Try to close the window after a short delay
            setTimeout(() => {
              try {
                newWindow.close();
              } catch (e) {
                console.log('Could not close window');
              }
            }, 3000);
            
            console.log(`✅ Android window.open successful: ${filename}`);
            return;
          }
        } catch (error) {
          console.error(`❌ Android window.open failed: ${error}`);
        }
      }
    }
    
    // Method 3: Desktop/Universal - Direct link with proper filename
    try {
      console.log(`💻 Trying desktop direct link...`);
      
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      link.style.display = 'none';
      link.setAttribute('target', '_self');
      link.setAttribute('rel', 'noopener noreferrer');
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      console.log(`✅ Desktop direct link successful: ${filename}`);
      return;
      
    } catch (error) {
      console.error(`❌ Desktop direct link failed: ${error}`);
    }
    
    // Method 4: Aggressive link with event prevention
    try {
      console.log(`🔄 Trying aggressive link method...`);
      
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      link.style.display = 'none';
      link.setAttribute('target', '_self');
      link.setAttribute('rel', 'noopener noreferrer');
      
      // Prevent default behavior
      link.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
      });
      
      document.body.appendChild(link);
      
      // Force click
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
      
      console.log(`✅ Aggressive link successful: ${filename}`);
      return;
      
    } catch (error) {
      console.error(`❌ Aggressive link failed: ${error}`);
    }
    
    // Method 5: Form submission (last resort)
    try {
      console.log(`📝 Trying form submission...`);
      
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
      
      console.log(`✅ Form submission successful: ${filename}`);
      return;
      
    } catch (error) {
      console.error(`❌ Form submission failed: ${error}`);
    }
    
    throw new Error('All download methods failed');
    
  } catch (error) {
    console.error(`❌ Download failed: ${error}`);
    // Don't open in new tab - just show error
    alert('Download failed. Please try again.');
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
