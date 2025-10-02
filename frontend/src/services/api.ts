import axios from 'axios';

const API_BASE_URL = 'https://certificate-tb.onrender.com';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minutes
  withCredentials: true,
});

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

// Mobile-optimized download function
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
    
    // Detect device type
    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
    const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
    const isAndroid = /Android/.test(navigator.userAgent);
    
    console.log(`📱 Device Info: Mobile=${isMobile}, iOS=${isIOS}, Android=${isAndroid}`);
    
    // Method 1: iOS Web Share API (best for iOS)
    if (isIOS && navigator.share) {
      try {
        console.log(`📱 Trying iOS Web Share API...`);
        
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
    
    // Method 2: Mobile blob download (works on most mobile browsers)
    if (isMobile) {
      try {
        console.log(`📱 Trying mobile blob download...`);
        
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
          
          // Add mobile-specific attributes
          link.setAttribute('download', filename);
          link.setAttribute('target', '_self');
          link.setAttribute('rel', 'noopener noreferrer');
          
          // Add touch events for mobile
          link.addEventListener('touchstart', (e) => {
            e.preventDefault();
            e.stopPropagation();
          });
          
          link.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation();
          });
          
          document.body.appendChild(link);
          
          // Trigger download
          link.click();
          
          // Clean up after a short delay
          setTimeout(() => {
            document.body.removeChild(link);
            URL.revokeObjectURL(blobUrl);
          }, 1000);
          
          console.log(`✅ Mobile blob download successful: ${filename}`);
          return;
        }
      } catch (error) {
        console.error(`❌ Mobile blob download failed: ${error}`);
      }
    }
    
    // Method 3: Android-specific window.open
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
    
    // Method 4: Universal fallback - direct link
    try {
      console.log(`💻 Trying universal direct link...`);
      
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      link.style.display = 'none';
      
      // Set attributes for download
      link.setAttribute('download', filename);
      link.setAttribute('target', '_self');
      link.setAttribute('rel', 'noopener noreferrer');
      
      // Prevent navigation
      link.addEventListener('click', (e) => {
        e.preventDefault();
        e.stopPropagation();
      });
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      console.log(`✅ Universal direct link successful: ${filename}`);
      return;
      
    } catch (error) {
      console.error(`❌ Universal direct link failed: ${error}`);
    }
    
    throw new Error('All download methods failed');
    
  } catch (error) {
    console.error(`❌ Download failed: ${error}`);
    alert('Download failed. Please try again.');
  }
};

// Student Details API
export const getStudentDetails = async () => {
  const response = await api.get('/api/students');
  return response.data;
};

// Bulk Certificate Generation API
export const bulkGenerateCertificates = async (data: any) => {
  const bulkApi = axios.create({
    baseURL: API_BASE_URL,
    timeout: 600000, // 10 minutes for bulk operations
    withCredentials: true,
  });
  
  const response = await bulkApi.post('/api/certificates/bulk-generate', data, {
    headers: {
      'Content-Type': 'application/json',
    },
  });
  return response.data;
};

export const updateStudentDetails = async (certificateId: string, studentData: any) => {
  const response = await api.put(`/api/students/${certificateId}`, studentData);
  return response.data;
};

export default api;
