/**
 * Download utilities for both web and mobile
 * Handles automatic downloads with proper file naming and mobile compatibility
 */

export interface DownloadOptions {
  url: string;
  filename: string;
  mimeType?: string;
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
  const { url, filename, mimeType = 'image/png' } = options;
  
  try {
    if (isMobile()) {
      await downloadOnMobile(url, filename, mimeType);
    } else {
      await downloadOnDesktop(url, filename, mimeType);
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
    // Fetch the file
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const blob = await response.blob();
    
    // Create download link
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    link.style.display = 'none';
    
    // Trigger download
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Clean up
    window.URL.revokeObjectURL(downloadUrl);
    
    console.log(`✅ Desktop download completed: ${filename}`);
  } catch (error) {
    console.error('Desktop download failed:', error);
    throw error;
  }
};

/**
 * Download on mobile devices
 */
const downloadOnMobile = async (url: string, filename: string, mimeType: string): Promise<void> => {
  try {
    if (isIOS()) {
      await downloadOnIOS(url, filename, mimeType);
    } else if (isAndroid()) {
      await downloadOnAndroid(url, filename, mimeType);
    } else {
      // Generic mobile fallback
      await downloadOnGenericMobile(url, filename, mimeType);
    }
  } catch (error) {
    console.error('Mobile download failed:', error);
    throw error;
  }
};

/**
 * Download on iOS devices
 */
const downloadOnIOS = async (url: string, filename: string, mimeType: string): Promise<void> => {
  try {
    // For iOS, we need to open the image in a new tab and let user save manually
    // or use a more sophisticated approach with Web Share API
    if (navigator.share && navigator.canShare) {
      // Try Web Share API first (iOS 12.2+)
      const response = await fetch(url);
      const blob = await response.blob();
      const file = new File([blob], filename, { type: mimeType });
      
      if (navigator.canShare({ files: [file] })) {
        await navigator.share({
          files: [file],
          title: filename,
        });
        console.log(`✅ iOS Web Share download completed: ${filename}`);
        return;
      }
    }
    
    // Fallback: Open in new tab for manual save
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
const downloadOnAndroid = async (url: string, filename: string, _mimeType: string): Promise<void> => {
  try {
    // Fetch the file
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const blob = await response.blob();
    
    // Try to trigger download using blob URL
    const downloadUrl = window.URL.createObjectURL(blob);
    
    // Create a temporary link and trigger click
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // Clean up
    window.URL.revokeObjectURL(downloadUrl);
    
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
const downloadOnGenericMobile = async (url: string, filename: string, _mimeType: string): Promise<void> => {
  try {
    // Try the same approach as Android
    const response = await fetch(url);
    const blob = await response.blob();
    
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename;
    link.style.display = 'none';
    
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    window.URL.revokeObjectURL(downloadUrl);
    
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
  const filename = generateFilename(`Certificate_${studentName.replace(/\s+/g, '_')}`, 'png');
  
  await downloadFile({
    url: certificateUrl,
    filename: filename,
    mimeType: 'image/png'
  });
};

/**
 * Download QR code with automatic filename generation
 */
export const downloadQRCode = async (qrUrl: string, studentName: string): Promise<void> => {
  const filename = generateFilename(`QR_${studentName.replace(/\s+/g, '_')}`, 'png');
  
  await downloadFile({
    url: qrUrl,
    filename: filename,
    mimeType: 'image/png'
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
