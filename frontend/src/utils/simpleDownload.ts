/**
 * Simple and robust download utility for certificates
 * This file provides a more reliable download mechanism
 */

/**
 * Download certificate with forced local download
 */
export const downloadCertificateSimple = async (certificateUrl: string, studentName: string): Promise<void> => {
  // Clean and format student name for filename
  const cleanName = studentName
    .trim()
    .replace(/\s+/g, '_')  // Replace spaces with underscores
    .replace(/[^a-zA-Z0-9_]/g, '')  // Remove special characters
    .substring(0, 50);  // Limit length to 50 characters
  
  // Create filename with student name prominently displayed
  const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
  const filename = `Certificate_${cleanName}_${timestamp}.png`;
  
  console.log(`📜 Downloading certificate for: ${studentName} as ${filename}`);
  console.log(`🔗 Original URL: ${certificateUrl}`);
  
  // Convert Google Drive URLs to direct download URLs
  let downloadUrl = certificateUrl;
  
  // Handle Google Drive thumbnail URLs
  if (certificateUrl.includes('drive.google.com/thumbnail')) {
    const fileIdMatch = certificateUrl.match(/[?&]id=([^&]+)/);
    if (fileIdMatch) {
      const fileId = fileIdMatch[1];
      downloadUrl = `https://drive.google.com/uc?id=${fileId}&export=download`;
      console.log(`🔄 Converted thumbnail URL to download URL: ${downloadUrl}`);
    }
  }
  
  // Handle Google Drive sharing URLs
  else if (certificateUrl.includes('lh3.googleusercontent.com')) {
    const fileIdMatch = certificateUrl.match(/\/d\/([^\/]+)/);
    if (fileIdMatch) {
      const fileId = fileIdMatch[1];
      downloadUrl = `https://drive.google.com/uc?id=${fileId}&export=download`;
      console.log(`🔄 Converted sharing URL to download URL: ${downloadUrl}`);
    }
  }
  
  // Try multiple download methods
  let success = false;
  
  // Method 1: Direct fetch with blob
  try {
    console.log('🔄 Method 1: Direct fetch with blob...');
    const response = await fetch(downloadUrl, {
      method: 'GET',
      mode: 'cors',
      credentials: 'omit',
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const blob = await response.blob();
    console.log(`📦 Blob created: ${blob.size} bytes, type: ${blob.type}`);
    
    // Create download link
    const blobUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = blobUrl;
    link.download = filename;
    link.style.display = 'none';
    
    // Trigger download
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Clean up
    setTimeout(() => {
      window.URL.revokeObjectURL(blobUrl);
    }, 1000);
    
    console.log(`✅ Method 1 successful: ${filename}`);
    success = true;
    
  } catch (error) {
    console.error(`❌ Method 1 failed: ${error}`);
  }
  
  // Method 2: Simple link download
  if (!success) {
    try {
      console.log('🔄 Method 2: Simple link download...');
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.download = filename;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.style.display = 'none';
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      
      console.log(`✅ Method 2 successful: ${filename}`);
      success = true;
      
    } catch (error) {
      console.error(`❌ Method 2 failed: ${error}`);
    }
  }
  
  // Method 3: Force download with iframe
  if (!success) {
    try {
      console.log('🔄 Method 3: Iframe download...');
      const iframe = document.createElement('iframe');
      iframe.style.display = 'none';
      iframe.style.width = '0';
      iframe.style.height = '0';
      iframe.src = downloadUrl;
      
      document.body.appendChild(iframe);
      
      // Remove iframe after delay
      setTimeout(() => {
        if (document.body.contains(iframe)) {
          document.body.removeChild(iframe);
        }
      }, 3000);
      
      console.log(`✅ Method 3 successful: ${filename}`);
      success = true;
      
    } catch (error) {
      console.error(`❌ Method 3 failed: ${error}`);
    }
  }
  
  // Method 4: Window.open as last resort
  if (!success) {
    console.log('🔄 Method 4: Opening in new window...');
    const newWindow = window.open(downloadUrl, '_blank');
    if (newWindow) {
      console.log(`✅ Method 4 successful: ${filename}`);
      success = true;
    } else {
      console.error(`❌ Method 4 failed: Popup blocked`);
    }
  }
  
  // Show result to user
  if (success) {
    console.log(`🎉 Certificate download initiated: ${filename}`);
  } else {
    console.error(`💥 All download methods failed`);
    alert(`Unable to download certificate automatically. Please try right-clicking the certificate image and selecting "Save As".`);
  }
};
