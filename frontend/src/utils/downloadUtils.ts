/**
 * Download utilities for both web and mobile
 * Handles automatic downloads with proper file naming and mobile compatibility
 */

export interface DownloadOptions {
  url: string;
  filename: string;
  __mimeType?: string;
}

/**
 * Detect if the device is mobile
 */
export const isMobile = (): boolean => {
  return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
    navigator.userAgent
  );
};

/**
 * Detect if the device is iOS
 */
export const isIOS = (): boolean => {
  return /iPad|iPhone|iPod/.test(navigator.userAgent);
};

/**
 * Detect if the device is Android
 */
export const isAndroid = (): boolean => {
  return /Android/.test(navigator.userAgent);
};

/**
 * Generate a proper filename with timestamp
 */
export const generateFilename = (baseName: string, extension: string = 'png'): string => {
  const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
  return `${baseName}_${timestamp}.${extension}`;
};

/**
 * Download file with automatic detection for mobile vs desktop
 */
export const downloadFile = async (options: DownloadOptions): Promise<void> => {
  const { url, filename, __mimeType = 'image/png' } = options;
  
  try {
    if (isMobile()) {
      await downloadOnMobile(url, filename, __mimeType);
    } else {
      await downloadOnDesktop(url, filename, __mimeType);
    }
  } catch (error) {
    console.error('Download failed:', error);
    // Fallback to opening in new tab
    window.open(url, '_blank');
  }
};

/**
 * Download on desktop browsers
 */
const downloadOnDesktop = async (url: string, filename: string, _mimeType: string): Promise<void> => {
  try {
    console.log(`📥 Starting download: ${filename} from ${url}`);
    
    // Method 1: Try using a hidden iframe to bypass CORS
    console.log('🔄 Trying iframe download method...');
    const iframe = document.createElement('iframe');
    iframe.style.display = 'none';
    iframe.style.width = '0';
    iframe.style.height = '0';
    iframe.style.border = 'none';
    
    // Set the iframe source to trigger download
    iframe.src = url;
    document.body.appendChild(iframe);
    
    // Clean up iframe after a delay
    setTimeout(() => {
      if (document.body.contains(iframe)) {
        document.body.removeChild(iframe);
      }
    }, 5000);
    
    console.log(`✅ Iframe download triggered: ${filename}`);
    
  } catch (error) {
    console.error('Iframe download failed:', error);
    
    // Method 2: Try direct link download
    console.log('🔄 Trying direct link download method...');
    try {
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      link.target = '_blank';
      link.rel = 'noopener noreferrer';
      link.style.display = 'none';
      
      // Add additional attributes for better download support
      link.setAttribute('download', filename);
      link.setAttribute('target', '_blank');
      link.setAttribute('rel', 'noopener noreferrer');
      
      document.body.appendChild(link);
      
      // Use a small delay to ensure the link is properly attached
      setTimeout(() => {
        link.click();
        if (document.body.contains(link)) {
          document.body.removeChild(link);
        }
      }, 10);
      
      console.log('✅ Direct link download triggered');
    } catch (fallbackError) {
      console.error('Direct link download also failed:', fallbackError);
      
      // Method 3: Final fallback - open in new tab
      console.log('🔄 Final fallback: opening in new tab...');
      window.open(url, '_blank');
      throw error;
    }
  }
};

/**
 * Download on mobile devices
 */
const downloadOnMobile = async (url: string, filename: string, mimeType: string): Promise<void> => {
  try {
    console.log(`📱 Starting mobile download: ${filename} from ${url}`);
    
    // For mobile, try direct link approach first (most reliable)
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.style.display = 'none';
    
    // Add additional attributes for better download support
    link.setAttribute('download', filename);
    link.setAttribute('target', '_blank');
    link.setAttribute('rel', 'noopener noreferrer');
    
    document.body.appendChild(link);
    
    // Use a small delay to ensure the link is properly attached
    setTimeout(() => {
      link.click();
      if (document.body.contains(link)) {
        document.body.removeChild(link);
      }
    }, 10);
    
    console.log('✅ Mobile download triggered');
    
  } catch (error) {
    console.error('Mobile download failed:', error);
    
    // Fallback: Try platform-specific methods
    try {
      if (isIOS()) {
        await downloadOnIOS(url, filename, mimeType);
      } else if (isAndroid()) {
        await downloadOnAndroid(url, filename, mimeType);
      } else {
        // Generic mobile fallback
        await downloadOnGenericMobile(url, filename, mimeType);
      }
    } catch (fallbackError) {
      console.error('Platform-specific download also failed:', fallbackError);
      // Final fallback: open in new tab
      window.open(url, '_blank');
      throw error;
    }
  }
};

/**
 * Download on iOS devices
 */
const downloadOnIOS = async (url: string, filename: string, mimeType: string): Promise<void> => {
  try {
    console.log(`🍎 iOS download: ${filename} from ${url}`);
    
    // For iOS, we need to open the image in a new tab and let user save manually
    // or use a more sophisticated approach with Web Share API
    if (navigator.share && navigator.canShare) {
      // Try Web Share API first (iOS 12.2+)
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': mimeType,
        },
        mode: 'cors',
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const blob = await response.blob();
      console.log(`📦 iOS blob: ${blob.size} bytes, type: ${blob.type}`);
      
      // Ensure proper MIME type
      const finalBlob = new Blob([blob], { type: mimeType });
      const file = new File([finalBlob], filename, { type: mimeType });
      
      if (navigator.canShare({ files: [file] })) {
        await navigator.share({
          files: [file],
          title: filename,
        });
        console.log(`✅ iOS Web Share download completed: ${filename}`);
        return;
      }
    }
    
    // Fallback: Try blob download first, then open in new tab
    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': mimeType,
        },
        mode: 'cors',
      });
      
      if (response.ok) {
        const blob = await response.blob();
        const finalBlob = new Blob([blob], { type: mimeType });
        const downloadUrl = window.URL.createObjectURL(finalBlob);
        
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = filename;
        link.style.display = 'none';
        link.setAttribute('download', filename);
        
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        setTimeout(() => {
          window.URL.revokeObjectURL(downloadUrl);
        }, 100);
        
        console.log(`✅ iOS blob download completed: ${filename}`);
        return;
      }
    } catch (blobError) {
      console.log('iOS blob download failed, trying new tab fallback:', blobError);
    }
    
    // Final fallback: Open in new tab for manual save
    const newWindow = window.open(url, '_blank');
    if (newWindow) {
      newWindow.focus();
      console.log(`📱 iOS fallback: Opened ${filename} in new tab for manual save`);
    } else {
      throw new Error('Failed to open new window');
    }
  } catch (error) {
    console.error('iOS download failed:', error);
    throw error;
  }
};

/**
 * Download on Android devices
 */
const downloadOnAndroid = async (url: string, filename: string, mimeType: string): Promise<void> => {
  try {
    console.log(`📱 Android download: ${filename} from ${url}`);
    
    // Fetch the file with proper headers
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': mimeType,
      },
      mode: 'cors',
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const blob = await response.blob();
    console.log(`📦 Android blob: ${blob.size} bytes, type: ${blob.type}`);
    
    // Ensure proper MIME type
    const finalBlob = new Blob([blob], { type: mimeType });
    
    // Try to trigger download using blob URL
    const downloadUrl = window.URL.createObjectURL(finalBlob);
    
    // Create a temporary link and trigger click
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    link.style.display = 'none';
    link.setAttribute('download', filename);
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Clean up
    setTimeout(() => {
      window.URL.revokeObjectURL(downloadUrl);
    }, 100);
    
    console.log(`✅ Android download completed: ${filename}`);
  } catch (error) {
    console.error('Android download failed:', error);
    // Fallback: Open in new tab
    window.open(url, '_blank');
    throw error;
  }
};

/**
 * Download on generic mobile devices
 */
const downloadOnGenericMobile = async (url: string, filename: string, mimeType: string): Promise<void> => {
  try {
    console.log(`📱 Generic mobile download: ${filename} from ${url}`);
    
    // Try the same approach as Android
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Accept': mimeType,
      },
      mode: 'cors',
    });
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const blob = await response.blob();
    console.log(`📦 Generic mobile blob: ${blob.size} bytes, type: ${blob.type}`);
    
    // Ensure proper MIME type
    const finalBlob = new Blob([blob], { type: mimeType });
    
    const downloadUrl = window.URL.createObjectURL(finalBlob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    link.style.display = 'none';
    link.setAttribute('download', filename);
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    setTimeout(() => {
      window.URL.revokeObjectURL(downloadUrl);
    }, 100);
    
    console.log(`✅ Generic mobile download completed: ${filename}`);
  } catch (error) {
    console.error('Generic mobile download failed:', error);
    // Final fallback: Open in new tab
    window.open(url, '_blank');
    throw error;
  }
};

/**
 * Download certificate with automatic filename generation
 */
export const downloadCertificate = async (certificateUrl: string, studentName: string): Promise<void> => {
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
  console.log(`📝 Clean name: "${cleanName}"`);
  console.log(`⏰ Timestamp: ${timestamp}`);
  console.log(`📄 Final filename: "${filename}"`);
  
  // Convert display URL to download URL if it's a Google Drive thumbnail URL
  let downloadUrl = certificateUrl;
  if (certificateUrl.includes('drive.google.com/thumbnail') || certificateUrl.includes('lh3.googleusercontent.com')) {
    // Extract file ID from various Google Drive URL formats
    let fileId = null;
    
    // Try different URL patterns
    const patterns = [
      /[?&]id=([^&]+)/,  // Standard Google Drive URL
      /\/d\/([^\/]+)/,    // Google Drive sharing URL
      /\/file\/d\/([^\/]+)/, // Google Drive file URL
    ];
    
    for (const pattern of patterns) {
      const match = certificateUrl.match(pattern);
      if (match) {
        fileId = match[1];
        break;
      }
    }
    
    if (fileId) {
      downloadUrl = `https://drive.google.com/uc?id=${fileId}&export=download`;
      console.log(`🔄 Converted to download URL: ${downloadUrl}`);
    } else {
      console.log(`❌ Could not extract file ID from URL: ${certificateUrl}`);
      // Try alternative approach
      downloadUrl = certificateUrl.replace(/\/thumbnail\?.*/, '/uc?export=download');
      console.log(`🔄 Trying alternative URL conversion: ${downloadUrl}`);
    }
  } else {
    console.log(`📥 Using original URL for download: ${downloadUrl}`);
  }
  
  try {
    // Try the enhanced download method first
    await downloadFile({
      url: downloadUrl,
      filename: filename,
      __mimeType: 'image/png'
    });
    console.log(`✅ Certificate download completed successfully: ${filename}`);
    
  } catch (error) {
    console.error(`❌ Certificate download failed: ${error}`);
    // Show user-friendly error message
    const errorMessage = error instanceof Error ? error.message : 'Unable to download certificate. Please try again.';
    alert(`Download failed: ${errorMessage}`);
    
    // Fallback: Try iframe download method
    console.log('🔄 Attempting iframe download method...');
    try {
      const iframe = document.createElement('iframe');
      iframe.style.display = 'none';
      iframe.src = downloadUrl;
      document.body.appendChild(iframe);
      
      // Remove iframe after a delay
      setTimeout(() => {
        document.body.removeChild(iframe);
      }, 5000);
      
      console.log('✅ Iframe download method triggered');
    } catch (iframeError) {
      console.error('Iframe method failed:', iframeError);
      
      // Final fallback: Try opening in new tab
      console.log('🔄 Final fallback: opening in new tab');
      window.open(downloadUrl, '_blank');
    }
    
    throw error;
  }
};

/**
 * Simple and robust download certificate function
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
      // Try multiple Google Drive URL formats
      downloadUrl = `https://drive.google.com/file/d/${fileId}/view`;
      console.log(`🔄 Converted thumbnail URL to view URL: ${downloadUrl}`);
    }
  }
  
  // Handle Google Drive sharing URLs
  else if (certificateUrl.includes('lh3.googleusercontent.com')) {
    const fileIdMatch = certificateUrl.match(/\/d\/([^\/]+)/);
    if (fileIdMatch) {
      const fileId = fileIdMatch[1];
      downloadUrl = `https://drive.google.com/file/d/${fileId}/view`;
      console.log(`🔄 Converted sharing URL to view URL: ${downloadUrl}`);
    }
  }
  
  // Try multiple download methods
  let success = false;
  
  // Method 1: Direct link download (skip fetch for Google Drive URLs)
  try {
    console.log('🔄 Method 1: Direct link download...');
    
    // For Google Drive URLs, skip fetch and go directly to link download
    if (downloadUrl.includes('drive.google.com')) {
      console.log('📁 Google Drive URL detected, skipping fetch method');
      throw new Error('Google Drive URL - use direct download');
    }
    
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
  
  // Method 2: Simple link download with enhanced Google Drive handling
  if (!success) {
    try {
      console.log('🔄 Method 2: Simple link download...');
      
      // For Google Drive URLs, try a different approach
      if (downloadUrl.includes('drive.google.com')) {
        console.log('📁 Using Google Drive specific download method...');
        
        // Create a form to submit the download request
        const form = document.createElement('form');
        form.method = 'GET';
        form.action = downloadUrl;
        form.target = '_blank';
        form.style.display = 'none';
        
        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);
        
        console.log(`✅ Method 2 (Google Drive) successful: ${filename}`);
        success = true;
      } else {
        // Regular link download for non-Google Drive URLs
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
      }
      
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
    
    // For Google Drive URLs, try to open the file directly
    if (downloadUrl.includes('drive.google.com')) {
      console.log('📁 Opening Google Drive file in new tab...');
      
      // Try to open the file in a new tab where user can download
      const newWindow = window.open(downloadUrl, '_blank');
      if (newWindow) {
        console.log(`✅ Method 4 (Google Drive) successful: ${filename}`);
        success = true;
        
        // Show a helpful message to the user
        setTimeout(() => {
          alert(`Certificate opened in new tab. Please right-click on the image and select "Save image as..." to download with filename: ${filename}`);
        }, 1000);
      } else {
        console.error(`❌ Method 4 failed: Popup blocked`);
      }
    } else {
      const newWindow = window.open(downloadUrl, '_blank');
      if (newWindow) {
        console.log(`✅ Method 4 successful: ${filename}`);
        success = true;
      } else {
        console.error(`❌ Method 4 failed: Popup blocked`);
      }
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

/**
 * Download QR code with automatic filename generation
 */
export const downloadQRCode = async (qrUrl: string, studentName: string): Promise<void> => {
  // Clean and format student name for filename
  const cleanName = studentName
    .trim()
    .replace(/\s+/g, '_')  // Replace spaces with underscores
    .replace(/[^a-zA-Z0-9_]/g, '')  // Remove special characters
    .substring(0, 50);  // Limit length to 50 characters
  
  // Create filename with student name prominently displayed
  const timestamp = new Date().toISOString().slice(0, 19).replace(/[:-]/g, '');
  const filename = `QR_Code_${cleanName}_${timestamp}.png`;
  
  console.log(`📱 Downloading QR code for: ${studentName} as ${filename}`);
  
  // Convert display URL to download URL if it's a Google Drive thumbnail URL
  let downloadUrl = qrUrl;
  if (qrUrl.includes('drive.google.com/thumbnail')) {
    const fileIdMatch = qrUrl.match(/[?&]id=([^&]+)/);
    if (fileIdMatch) {
      const fileId = fileIdMatch[1];
      downloadUrl = `https://drive.google.com/uc?id=${fileId}&export=download`;
    }
  }
  
  await downloadFile({
    url: downloadUrl,
    filename: filename,
    __mimeType: 'image/png'
  });
};

/**
 * Download CSV file (for bulk results)
 */
export const downloadCSV = async (csvContent: string, filename: string): Promise<void> => {
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = window.URL.createObjectURL(blob);
  
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  link.style.display = 'none';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  window.URL.revokeObjectURL(url);
  
  console.log(`✅ CSV download completed: ${filename}`);
};
