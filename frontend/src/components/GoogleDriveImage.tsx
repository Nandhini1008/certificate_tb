import React, { useState, useEffect, useMemo, forwardRef } from "react";

interface GoogleDriveImageProps {
  src: string;
  alt: string;
  className?: string;
  fallbackComponent?: React.ReactNode;
  onLoad?: () => void;
  onError?: () => void;
}

const GoogleDriveImage = forwardRef<HTMLImageElement, GoogleDriveImageProps>(
  (
    {
      src,
      alt,
      className = "w-full h-full object-cover",
      fallbackComponent,
      onLoad,
      onError,
    },
    ref
  ) => {
    const [imageError, setImageError] = useState(false);
    const [imageLoaded, setImageLoaded] = useState(false);
    const [currentUrl, setCurrentUrl] = useState<string | null>(null);
    const [urlIndex, setUrlIndex] = useState(0);

    // Generate multiple URL formats to try
    const getUrlFormats = (url: string) => {
      if (!url || url.trim() === "") {
        return [];
      }
      
      // Try to extract file ID from various URL formats
      let fileId: string | null = null;
      
      // Pattern 1: ?id= or &id=
      const idMatch1 = url.match(/[?&]id=([^&]+)/);
      if (idMatch1) {
        fileId = idMatch1[1];
      }
      
      // Pattern 2: /d/FILE_ID/ or /file/d/FILE_ID/
      if (!fileId) {
        const idMatch2 = url.match(/\/d\/([^\/\?]+)/);
        if (idMatch2) {
          fileId = idMatch2[1];
        }
      }
      
      // Pattern 3: /uc?id=FILE_ID
      if (!fileId) {
        const idMatch3 = url.match(/\/uc\?id=([^&]+)/);
        if (idMatch3) {
          fileId = idMatch3[1];
        }
      }
      
      // Pattern 4: Extract from webContentLink format (uc?export=download&id=...)
      if (!fileId) {
        const idMatch4 = url.match(/export=download[&]?id=([^&]+)/);
        if (idMatch4) {
          fileId = idMatch4[1];
        }
      }
      
      // If we found a file ID, generate multiple URL formats
      if (fileId) {
        return [
          `https://drive.google.com/thumbnail?id=${fileId}&sz=w1000`,
          `https://drive.google.com/uc?export=view&id=${fileId}`,
          `https://drive.google.com/uc?id=${fileId}&export=download`,
          `https://lh3.googleusercontent.com/d/${fileId}`,
        ];
      }
      
      // If no file ID found, try the URL as-is
      return [url];
    };

    const urlFormats = useMemo(() => getUrlFormats(src), [src]);

    // Reset URL index when src changes
    useEffect(() => {
      setUrlIndex(0);
      setImageError(false);
      setImageLoaded(false);
    }, [src]);

    useEffect(() => {
      if (!src || src.trim() === "") {
        setCurrentUrl(null);
        setImageError(true);
        return;
      }
      
      if (urlFormats.length > 0 && urlIndex < urlFormats.length) {
        setCurrentUrl(urlFormats[urlIndex]);
        setImageError(false);
        setImageLoaded(false);
      } else if (urlFormats.length === 0) {
        setCurrentUrl(null);
        setImageError(true);
      }
    }, [src, urlIndex, urlFormats]);

    const handleError = () => {
      console.log(
        `Image failed to load (attempt ${urlIndex + 1}):`,
        currentUrl
      );

      // Try next URL format if available
      if (urlIndex < urlFormats.length - 1) {
        setUrlIndex(urlIndex + 1);
      } else {
        console.log("All URL formats failed, showing fallback");
        setImageError(true);
        onError?.();
      }
    };

    const handleLoad = () => {
      console.log("Image loaded successfully:", currentUrl);
      setImageLoaded(true);
      onLoad?.();
    };

    // Don't render image if no valid URL or if error occurred
    if (imageError || !currentUrl || currentUrl.trim() === "") {
      return (
        <div className="w-full h-full flex items-center justify-center text-gray-400 bg-gray-100">
          {fallbackComponent || (
            <div className="text-center">
              <div className="text-2xl mb-2">🖼️</div>
              <div className="text-sm">Image not available</div>
              {urlFormats.length > 0 && (
                <div className="text-xs mt-1 text-gray-300 break-all">
                  Tried: {urlFormats.join(", ")}
                </div>
              )}
            </div>
          )}
        </div>
      );
    }

    return (
      <img
        ref={ref}
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
  }
);

export default GoogleDriveImage;
