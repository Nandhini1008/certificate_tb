import axios from 'axios';

// Use environment variable for API URL - REQUIRED
export const API_BASE_URL = import.meta.env.VITE_API_URL;
if (!API_BASE_URL) {
  throw new Error('VITE_API_URL environment variable is required. Please set it in .env.local file.');
}

// When using ngrok or when backend allows all origins, credentials must be disabled
// This is a CORS requirement: allow_origins=["*"] requires allow_credentials=False
const isUsingNgrok = API_BASE_URL.includes('ngrok');
const shouldUseCredentials = !isUsingNgrok && !API_BASE_URL.includes('onrender.com');

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes
  withCredentials: shouldUseCredentials,
});

// Add ngrok-skip-browser-warning header if using ngrok
if (isUsingNgrok) {
  api.defaults.headers.common['ngrok-skip-browser-warning'] = 'true';
}

// Add request interceptor to ensure ngrok header is always present
api.interceptors.request.use(
  (config) => {
    // Add ngrok header if using ngrok URL
    if (config.baseURL?.includes('ngrok') || config.url?.includes('ngrok')) {
      config.headers['ngrok-skip-browser-warning'] = 'true';
      // Disable credentials for ngrok requests
      config.withCredentials = false;
    }
    return config;
  },
  (error) => {
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
  const timestamp = Date.now();
  const response = await api.get(`/api/templates?t=${timestamp}`);
  return response.data;
};

// Certificate API
export const generateCertificate = async (data: any) => {
  const response = await api.post('/api/certificates/generate', data, {
    headers: {
      'Content-Type': 'application/json',
    },
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

// Device-specific download function
export const downloadCertificateDirect = async (imageUrl: string, studentName: string): Promise<void> => {
  try {
    console.log(`🔗 Image URL: ${imageUrl}`);
    console.log(`👤 Student Name: ${studentName}`);
    
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
    
    console.log(`📁 Final Filename: ${filename}`);
    
    // Enhanced device detection
    const userAgent = navigator.userAgent;
    const isIOS = /iPad|iPhone|iPod/.test(userAgent);
    const isAndroid = /Android/.test(userAgent);
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent);
    const isDesktop = !isMobile;
    
    console.log(`📱 Device Detection:`);
    console.log(`   User Agent: ${userAgent}`);
    console.log(`   iOS: ${isIOS}`);
    console.log(`   Android: ${isAndroid}`);
    console.log(`   Mobile: ${isMobile}`);
    console.log(`   Desktop: ${isDesktop}`);
    
    // Method 1: iOS Web Share API (best for iOS)
    if (isIOS && navigator.share) {
      try {
        console.log(`🍎 iOS detected - using Web Share API`);
        
        const response = await fetch(downloadUrl, { 
          mode: 'cors',
          headers: {
            'Accept': 'image/png,image/jpeg,image/*,*/*',
            'Cache-Control': 'no-cache'
          }
        });
        
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
    
    // Method 2: Android-specific download
    if (isAndroid) {
      try {
        console.log(`🤖 Android detected - using blob download`);
        
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
          
          // Android-specific attributes
          link.setAttribute('download', filename);
          link.setAttribute('target', '_blank');
          link.setAttribute('rel', 'noopener noreferrer');
          
          document.body.appendChild(link);
          link.click();
          
          // Clean up
          setTimeout(() => {
            document.body.removeChild(link);
            URL.revokeObjectURL(blobUrl);
          }, 2000);
          
          console.log(`✅ Android blob download successful: ${filename}`);
          return;
        }
      } catch (error) {
        console.error(`❌ Android blob download failed: ${error}`);
        
        // Fallback: Android window.open
        try {
          console.log(`🤖 Android fallback - using window.open`);
          const newWindow = window.open(downloadUrl, '_blank', 'noopener,noreferrer');
          if (newWindow) {
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
    
    // Method 3: Other mobile devices
    if (isMobile && !isIOS && !isAndroid) {
      try {
        console.log(`📱 Other mobile device detected - using blob download`);
        
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
          
          link.setAttribute('download', filename);
          link.setAttribute('target', '_self');
          link.setAttribute('rel', 'noopener noreferrer');
          
          document.body.appendChild(link);
          link.click();
          
          setTimeout(() => {
            document.body.removeChild(link);
            URL.revokeObjectURL(blobUrl);
          }, 2000);
          
          console.log(`✅ Other mobile blob download successful: ${filename}`);
          return;
        }
      } catch (error) {
        console.error(`❌ Other mobile blob download failed: ${error}`);
      }
    }
    
    // Method 4: Desktop download
    if (isDesktop) {
      try {
        console.log(`💻 Desktop detected - using direct link`);
        
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = filename;
        link.style.display = 'none';
        
        link.setAttribute('download', filename);
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
    }
    
    // Method 5: Universal fallback
    try {
      console.log(`🔄 Universal fallback - trying all methods`);
      
      // Try blob download first
      try {
        const response = await fetch(downloadUrl, { mode: 'cors' });
        if (response.ok) {
          const blob = await response.blob();
          const blobUrl = URL.createObjectURL(blob);
          
          const link = document.createElement('a');
          link.href = blobUrl;
          link.download = filename;
          link.style.display = 'none';
          
          document.body.appendChild(link);
          link.click();
          
          setTimeout(() => {
            document.body.removeChild(link);
            URL.revokeObjectURL(blobUrl);
          }, 2000);
          
          console.log(`✅ Universal blob download successful: ${filename}`);
          return;
        }
      } catch (error) {
        console.error(`❌ Universal blob download failed: ${error}`);
      }
      
      // Try direct link
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      link.style.display = 'none';
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      console.log(`✅ Universal direct link successful: ${filename}`);
      return;
      
    } catch (error) {
      console.error(`❌ Universal fallback failed: ${error}`);
    }
    
    throw new Error('All download methods failed');
    
  } catch (error) {
    console.error(`❌ Download failed: ${error}`);
    const errorMessage = error instanceof Error ? error.message : 'Unknown error';
    alert(`Download failed: ${errorMessage}. Please try again.`);
  }
};

// Student Details API
export const getStudentDetails = async () => {
  const response = await api.get('/api/students');
  return response.data;
};

// Bulk Certificate Generation API
export const bulkGenerateCertificates = async (
  data: { templateId: string; csvFile: File; deviceType?: string }
) => {
  const formData = new FormData();
  formData.append('template_id', data.templateId);
  formData.append('csv_file', data.csvFile);
  formData.append('device_type', data.deviceType ?? 'desktop');

  const bulkApi = axios.create({
    baseURL: API_BASE_URL,
    timeout: 600000, // 10 minutes for bulk operations
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
