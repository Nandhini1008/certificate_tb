import React, { useState } from "react";

interface GoogleDriveImageProps {
  src: string;
  alt: string;
  className?: string;
  fallbackComponent?: React.ReactNode;
}

const GoogleDriveImage: React.FC<GoogleDriveImageProps> = ({
  src,
  alt,
  className = "w-full h-full object-cover",
  fallbackComponent,
}) => {
  const [imageError, setImageError] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);

  // Convert Google Drive URL to thumbnail format if needed
  const getOptimizedUrl = (url: string) => {
    if (url.includes("drive.google.com")) {
      // Extract file ID from various Google Drive URL formats
      const fileIdMatch = url.match(/[?&]id=([^&]+)/);
      if (fileIdMatch) {
        const fileId = fileIdMatch[1];
        return `https://drive.google.com/thumbnail?id=${fileId}&sz=w1000`;
      }
    }
    return url;
  };

  const optimizedSrc = getOptimizedUrl(src);

  const handleError = () => {
    console.log("Image failed to load:", optimizedSrc);
    setImageError(true);
  };

  const handleLoad = () => {
    console.log("Image loaded successfully:", optimizedSrc);
    setImageLoaded(true);
  };

  if (imageError) {
    return (
      <div className="w-full h-full flex items-center justify-center text-gray-400 bg-gray-100">
        {fallbackComponent || (
          <div className="text-center">
            <div className="text-2xl mb-2">🖼️</div>
            <div className="text-sm">Image not available</div>
            <div className="text-xs mt-1 text-gray-300 break-all">
              {optimizedSrc}
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <img
      src={optimizedSrc}
      alt={alt}
      className={className}
      loading="lazy"
      crossOrigin="anonymous"
      onError={handleError}
      onLoad={handleLoad}
      style={{
        opacity: imageLoaded ? 1 : 0,
        transition: "opacity 0.3s ease-in-out",
      }}
    />
  );
};

export default GoogleDriveImage;