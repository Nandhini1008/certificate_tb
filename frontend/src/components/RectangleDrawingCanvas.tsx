import React, { useState, useRef, useEffect } from "react";
import GoogleDriveImage from "./GoogleDriveImage";

interface Rectangle {
  id: string;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  type: "name" | "date" | "certificate_no";
  label: string;
}

interface RectangleDrawingCanvasProps {
  imageUrl: string;
  onRectangleComplete: (rectangle: Rectangle) => void;
  existingRectangles: Rectangle[];
  selectedType: "name" | "date" | "certificate_no" | null;
  onRectangleUpdate: (rectangles: Rectangle[]) => void;
}

const RectangleDrawingCanvas: React.FC<RectangleDrawingCanvasProps> = ({
  imageUrl,
  onRectangleComplete,
  existingRectangles,
  selectedType,
  onRectangleUpdate,
}) => {
  console.log("DEBUG: RectangleDrawingCanvas received imageUrl:", imageUrl);
  const [isDrawing, setIsDrawing] = useState(false);
  const [startPoint, setStartPoint] = useState<{ x: number; y: number } | null>(
    null
  );
  const [currentRect, setCurrentRect] = useState<Rectangle | null>(null);
  const [rectangles, setRectangles] = useState<Rectangle[]>(existingRectangles);
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageDimensions, setImageDimensions] = useState({
    width: 0,
    height: 0,
  });
  const [originalImageDimensions, setOriginalImageDimensions] = useState({
    width: 0,
    height: 0,
  });

  const canvasRef = useRef<HTMLDivElement>(null);
  const imageRef = useRef<HTMLImageElement>(null);

  useEffect(() => {
    setRectangles(existingRectangles);
  }, [existingRectangles]);

  const handleImageLoad = () => {
    console.log("DEBUG: Image loaded successfully");
    if (imageRef.current) {
      // Get displayed dimensions
      const displayedWidth = imageRef.current.offsetWidth;
      const displayedHeight = imageRef.current.offsetHeight;

      // Get original image dimensions
      const originalWidth = imageRef.current.naturalWidth;
      const originalHeight = imageRef.current.naturalHeight;

      console.log(
        "DEBUG: Image dimensions - Displayed:",
        displayedWidth,
        "x",
        displayedHeight
      );
      console.log(
        "DEBUG: Image dimensions - Original:",
        originalWidth,
        "x",
        originalHeight
      );

      setImageDimensions({
        width: displayedWidth,
        height: displayedHeight,
      });

      setOriginalImageDimensions({
        width: originalWidth,
        height: originalHeight,
      });

      setImageLoaded(true);
    }
  };

  const getMousePosition = (e: React.MouseEvent) => {
    if (!canvasRef.current) return { x: 0, y: 0 };

    const rect = canvasRef.current.getBoundingClientRect();
    return {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    };
  };

  const scaleCoordinatesToOriginal = (x: number, y: number) => {
    if (
      originalImageDimensions.width === 0 ||
      originalImageDimensions.height === 0
    ) {
      return { x, y };
    }

    const scaleX = originalImageDimensions.width / imageDimensions.width;
    const scaleY = originalImageDimensions.height / imageDimensions.height;

    return {
      x: Math.round(x * scaleX),
      y: Math.round(y * scaleY),
    };
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    if (!selectedType || !imageLoaded) return;

    const { x, y } = getMousePosition(e);
    setIsDrawing(true);
    setStartPoint({ x, y });

    // Store display coordinates for current drawing
    const newRect: Rectangle = {
      id: `rect_${Date.now()}`,
      x1: x,
      y1: y,
      x2: x,
      y2: y,
      type: selectedType,
      label: selectedType.replace("_", " ").toUpperCase(),
    };

    setCurrentRect(newRect);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDrawing || !currentRect || !startPoint) return;

    const { x, y } = getMousePosition(e);

    const updatedRect = {
      ...currentRect,
      x2: x,
      y2: y,
    };

    setCurrentRect(updatedRect);
  };

  const handleMouseUp = () => {
    if (!isDrawing || !currentRect || !startPoint) return;

    // Normalize rectangle coordinates (ensure x1,y1 is top-left and x2,y2 is bottom-right)
    const normalizedRect = {
      ...currentRect,
      x1: Math.min(currentRect.x1, currentRect.x2),
      y1: Math.min(currentRect.y1, currentRect.y2),
      x2: Math.max(currentRect.x1, currentRect.x2),
      y2: Math.max(currentRect.y1, currentRect.y2),
    };

    // Only create rectangle if it has minimum size
    if (
      Math.abs(normalizedRect.x2 - normalizedRect.x1) > 10 &&
      Math.abs(normalizedRect.y2 - normalizedRect.y1) > 10
    ) {
      // Scale coordinates to original image size
      const scaledCoords1 = scaleCoordinatesToOriginal(
        normalizedRect.x1,
        normalizedRect.y1
      );
      const scaledCoords2 = scaleCoordinatesToOriginal(
        normalizedRect.x2,
        normalizedRect.y2
      );

      console.log("DEBUG: Original coordinates:", normalizedRect);
      console.log("DEBUG: Scaled coordinates:", {
        x1: scaledCoords1.x,
        y1: scaledCoords1.y,
        x2: scaledCoords2.x,
        y2: scaledCoords2.y,
      });
      console.log(
        "DEBUG: Image scaling - Displayed:",
        imageDimensions,
        "Original:",
        originalImageDimensions
      );

      const scaledRect = {
        ...normalizedRect,
        x1: scaledCoords1.x,
        y1: scaledCoords1.y,
        x2: scaledCoords2.x,
        y2: scaledCoords2.y,
      };

      const newRectangles = [...rectangles, scaledRect];
      setRectangles(newRectangles);
      onRectangleUpdate(newRectangles);
      onRectangleComplete(scaledRect);
    }

    setIsDrawing(false);
    setStartPoint(null);
    setCurrentRect(null);
  };

  const handleRectangleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    // You can add rectangle selection/editing logic here
  };

  const deleteRectangle = (rectId: string) => {
    const newRectangles = rectangles.filter((rect) => rect.id !== rectId);
    setRectangles(newRectangles);
    onRectangleUpdate(newRectangles);
  };

  const getRectangleStyle = (rect: Rectangle, isCurrent: boolean = false) => {
    let displayX1 = rect.x1;
    let displayY1 = rect.y1;
    let displayX2 = rect.x2;
    let displayY2 = rect.y2;

    // For current drawing rectangle, use coordinates as-is (they're already in display coordinates)
    // For saved rectangles, scale from original image coordinates to display coordinates
    if (
      !isCurrent &&
      originalImageDimensions.width > 0 &&
      originalImageDimensions.height > 0
    ) {
      const scaleX = imageDimensions.width / originalImageDimensions.width;
      const scaleY = imageDimensions.height / originalImageDimensions.height;

      displayX1 = rect.x1 * scaleX;
      displayY1 = rect.y1 * scaleY;
      displayX2 = rect.x2 * scaleX;
      displayY2 = rect.y2 * scaleY;
    }

    const width = Math.abs(displayX2 - displayX1);
    const height = Math.abs(displayY2 - displayY1);
    const left = Math.min(displayX1, displayX2);
    const top = Math.min(displayY1, displayY2);

    const colors = {
      name: "#3B82F6", // Blue
      date: "#10B981", // Green
      certificate_no: "#F59E0B", // Yellow
    };

    return {
      position: "absolute" as const,
      left: `${left}px`,
      top: `${top}px`,
      width: `${width}px`,
      height: `${height}px`,
      border: `2px solid ${colors[rect.type]}`,
      backgroundColor: `${colors[rect.type]}20`, // 20% opacity
      cursor: "pointer",
      zIndex: isCurrent ? 20 : 10,
      borderRadius: "4px",
    };
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case "name":
        return "NAME";
      case "date":
        return "DATE";
      case "certificate_no":
        return "CERT NO";
      default:
        return type.toUpperCase();
    }
  };

  return (
    <div className="space-y-4">
      <div className="text-sm text-gray-600">
        {selectedType ? (
          <p>
            Click and drag to draw a rectangle for{" "}
            <strong>{getTypeLabel(selectedType)}</strong> placement
          </p>
        ) : (
          <p>Select a field type above to start drawing rectangles</p>
        )}
      </div>

      <div className="relative border border-gray-300 rounded-lg overflow-hidden">
        <div
          ref={canvasRef}
          className="relative cursor-crosshair"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        >
          <GoogleDriveImage
            ref={imageRef}
            src={imageUrl}
            alt="Template"
            className="w-full h-auto select-none"
            onLoad={handleImageLoad}
            onError={() => {
              console.error("DEBUG: Image failed to load:", imageUrl);
            }}
            fallbackComponent={
              <div className="w-full h-64 bg-gray-100 flex items-center justify-center">
                <div className="text-center">
                  <div className="text-gray-400 text-4xl mb-2">🖼️</div>
                  <div className="text-lg text-gray-500">Template</div>
                  <div className="text-sm text-gray-400">
                    Image not available
                  </div>
                  <div className="text-xs text-gray-400 mt-1">
                    URL: {imageUrl}
                  </div>
                </div>
              </div>
            }
          />

          {/* Existing rectangles */}
          {rectangles.map((rect) => (
            <div key={rect.id}>
              <div
                style={getRectangleStyle(rect)}
                onClick={handleRectangleClick}
                className="group"
              >
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    deleteRectangle(rect.id);
                  }}
                  className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 text-white text-xs rounded-full opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center"
                >
                  ×
                </button>
              </div>
            </div>
          ))}

          {/* Current drawing rectangle */}
          {currentRect && (
            <div
              style={getRectangleStyle(currentRect, true)}
              className="border-dashed"
            ></div>
          )}
        </div>
      </div>

      {/* Rectangle list */}
      {rectangles.length > 0 && (
        <div className="space-y-2">
          <h4 className="text-sm font-medium text-gray-700">Defined Areas:</h4>
          <div className="space-y-1">
            {rectangles.map((rect) => (
              <div
                key={rect.id}
                className="flex items-center justify-between p-2 bg-gray-50 rounded border"
              >
                <div className="flex items-center space-x-2">
                  <div
                    className="w-3 h-3 rounded"
                    style={{
                      backgroundColor:
                        rect.type === "name"
                          ? "#3B82F6"
                          : rect.type === "date"
                          ? "#10B981"
                          : "#F59E0B",
                    }}
                  />
                  <span className="text-sm font-medium">
                    {getTypeLabel(rect.type)}
                  </span>
                  <span className="text-xs text-gray-500">
                    ({Math.abs(rect.x2 - rect.x1)}×{Math.abs(rect.y2 - rect.y1)}
                    )
                  </span>
                </div>
                <button
                  onClick={() => deleteRectangle(rect.id)}
                  className="text-red-500 hover:text-red-700 text-sm"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default RectangleDrawingCanvas;
