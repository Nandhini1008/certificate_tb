import React, { useState, useEffect } from "react";

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
  const [currentUrl, setCurrentUrl] = useState("");
  const [urlIndex, setUrlIndex] = useState(0);

  // Generate multiple URL formats to try
  const getUrlFormats = (url: string) => {
    if (url.includes("drive.google.com")) {
      const fileIdMatch = url.match(/[?&]id=([^&]+)/);
      if (fileIdMatch) {
        const fileId = fileIdMatch[1];
        return [
          `https://drive.google.com/uc?export=view&id=${fileId}`,
          `https://drive.google.com/thumbnail?id=${fileId}&sz=w1000`,
          `https://drive.google.com/uc?id=${fileId}&export=download`,
          `https://lh3.googleusercontent.com/d/${fileId}`,
        ];
      }
    }
    return [url];
  };

  const urlFormats = getUrlFormats(src);

  useEffect(() => {
    if (urlFormats.length > 0) {
      setCurrentUrl(urlFormats[urlIndex]);
    }
  }, [src, urlIndex]);

  const handleError = () => {
    console.log(`Image failed to load (attempt ${urlIndex + 1}):`, currentUrl);

    // Try next URL format if available
    if (urlIndex < urlFormats.length - 1) {
      setUrlIndex(urlIndex + 1);
    } else {
      console.log("All URL formats failed, showing fallback");
      setImageError(true);
    }
  };

  const handleLoad = () => {
    console.log("Image loaded successfully:", currentUrl);
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
              Tried: {urlFormats.join(", ")}
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <img
      src={currentUrl}
      alt={alt}
      className={className}
      loading="lazy"
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
