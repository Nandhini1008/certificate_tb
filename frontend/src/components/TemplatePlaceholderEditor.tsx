import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { MapPin, Save, RotateCcw, Square } from "lucide-react";
import { getTemplate, setTemplatePlaceholders } from "../services/api";
import RectangleDrawingCanvas from "./RectangleDrawingCanvas";
import GoogleDriveImage from "./GoogleDriveImage";

interface Placeholder {
  key: string;
  x: number;
  y: number;
  font: string;
  font_size: number;
  color: string;
  x1?: number;
  y1?: number;
  x2?: number;
  y2?: number;
  text_align?: string;
  vertical_align?: string;
}

interface Rectangle {
  id: string;
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  type: "name" | "date" | "certificate_no";
  label: string;
}

interface TemplatePlaceholderEditorProps {
  templateId: string;
}

const TemplatePlaceholderEditor: React.FC<TemplatePlaceholderEditorProps> = ({
  templateId,
}) => {
  const [template, setTemplate] = useState<any>(null);
  const [placeholders, setPlaceholders] = useState<Placeholder[]>([]);
  const [selectedPlaceholder, setSelectedPlaceholder] = useState<string | null>(
    null
  );
  const [selectedType, setSelectedType] = useState<
    "name" | "date" | "certificate_no" | null
  >(null);
  const [rectangles, setRectangles] = useState<Rectangle[]>([]);
  const [mode, setMode] = useState<"point" | "rectangle">("rectangle");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  const defaultPlaceholders: Placeholder[] = [
    {
      key: "student_name",
      x: 400,
      y: 300,
      font: "PlayfairDisplay-Bold.ttf",
      font_size: 48,
      color: "#0b2a4a",
    },
    {
      key: "course_name",
      x: 400,
      y: 380,
      font: "PlayfairDisplay-Bold.ttf",
      font_size: 36,
      color: "#0b2a4a",
    },
    {
      key: "date",
      x: 200,
      y: 500,
      font: "PlayfairDisplay-Bold.ttf",
      font_size: 24,
      color: "#0b2a4a",
    },
  ];

  useEffect(() => {
    console.log(
      "TemplatePlaceholderEditor mounted with templateId:",
      templateId
    );
    loadTemplate();
  }, [templateId]);

  const loadTemplate = async () => {
    try {
      setLoading(true);
      const templateData = await getTemplate(templateId);

      if (!templateData) {
        console.error("Template not found:", templateId);
        return;
      }

      console.log("Template data loaded:", templateData);
      console.log("Template image path:", templateData.image_path);
      console.log("Using Google Drive URL directly:", templateData.image_path);

      setTemplate(templateData);

      if (templateData.placeholders && templateData.placeholders.length > 0) {
        setPlaceholders(templateData.placeholders);
        setRectangles(
          convertPlaceholdersToRectangles(templateData.placeholders)
        );
      } else {
        setPlaceholders(defaultPlaceholders);
        setRectangles([]);
      }
    } catch (error) {
      console.error("Failed to load template:", error);
      setTemplate(null);
    } finally {
      setLoading(false);
    }
  };

  const handlePlaceholderChange = (
    key: string,
    field: keyof Placeholder,
    value: any
  ) => {
    console.log(`DEBUG: Changing ${field} for ${key} to ${value}`);
    setPlaceholders((prev) => {
      const updated = prev.map((p) =>
        p.key === key ? { ...p, [field]: value } : p
      );
      console.log(`DEBUG: Updated placeholders:`, updated);
      return updated;
    });
  };

  const handleRectangleComplete = (rectangle: Rectangle) => {
    console.log("DEBUG: Rectangle completed:", rectangle);

    // Convert rectangle to placeholder format
    const placeholderKey =
      rectangle.type === "name" ? "student_name" : rectangle.type;

    // Get existing placeholder settings or use defaults
    const existingPlaceholder = placeholders.find(
      (p) => p.key === placeholderKey
    );

    const placeholder: Placeholder = {
      key: placeholderKey,
      x: Math.round((rectangle.x1 + rectangle.x2) / 2), // Center point for backward compatibility
      y: Math.round((rectangle.y1 + rectangle.y2) / 2),
      font: "fonts/PlayfairDisplay-Bold.ttf",
      font_size:
        existingPlaceholder?.font_size ||
        (rectangle.type === "name" ? 48 : rectangle.type === "date" ? 18 : 16),
      color: existingPlaceholder?.color || "#0b2a4a",
      x1: Math.round(rectangle.x1),
      y1: Math.round(rectangle.y1),
      x2: Math.round(rectangle.x2),
      y2: Math.round(rectangle.y2),
      text_align:
        existingPlaceholder?.text_align ||
        (rectangle.type === "name" ? "center" : "left"),
      vertical_align: existingPlaceholder?.vertical_align || "center",
    };

    console.log("DEBUG: Converted placeholder:", placeholder);

    // Update or add placeholder
    setPlaceholders((prev) => {
      const existing = prev.find((p) => p.key === placeholder.key);
      if (existing) {
        const updated = prev.map((p) =>
          p.key === placeholder.key ? placeholder : p
        );
        console.log("DEBUG: Updated placeholders:", updated);
        return updated;
      } else {
        const added = [...prev, placeholder];
        console.log("DEBUG: Added placeholders:", added);
        return added;
      }
    });

    // Clear selection
    setSelectedType(null);
  };

  const handleRectangleUpdate = (updatedRectangles: Rectangle[]) => {
    setRectangles(updatedRectangles);
  };

  const convertPlaceholdersToRectangles = (
    placeholders: Placeholder[]
  ): Rectangle[] => {
    return placeholders
      .filter(
        (p) =>
          p.x1 !== undefined &&
          p.y1 !== undefined &&
          p.x2 !== undefined &&
          p.y2 !== undefined
      )
      .map((p) => ({
        id: `rect_${p.key}`,
        x1: p.x1!,
        y1: p.y1!,
        x2: p.x2!,
        y2: p.y2!,
        type:
          p.key === "student_name"
            ? "name"
            : (p.key as "date" | "certificate_no"),
        label: p.key.replace("_", " ").toUpperCase(),
      }));
  };


  const savePlaceholders = async () => {
    try {
      setSaving(true);
      console.log("DEBUG: Saving placeholders:", placeholders);
      console.log("DEBUG: Template ID:", templateId);

      // Log each placeholder's font size specifically
      placeholders.forEach((p) => {
        if (p.key === "date" || p.key === "certificate_no") {
          console.log(
            `DEBUG: ${p.key} font_size: ${p.font_size}, color: ${p.color}`
          );
        }
      });

      await setTemplatePlaceholders(templateId, placeholders);
      setSaved(true);
      setTimeout(() => setSaved(false), 3000);
    } catch (error: any) {
      console.error("Failed to save placeholders:", error);
      console.error("Error details:", error.response?.data);
      console.error("Error status:", error.response?.status);
      console.error("Error message:", error.message);
    } finally {
      setSaving(false);
    }
  };

  const resetPlaceholders = () => {
    setPlaceholders(defaultPlaceholders);
  };

  if (loading) {
    return (
      <motion.div
        className="card p-6"
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </motion.div>
    );
  }

  if (!template) {
    return (
      <motion.div
        className="card p-6"
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        <div className="text-center">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">
            Template Not Found
          </h3>
          <p className="text-gray-600 mb-4">
            The template with ID "{templateId}" could not be found.
          </p>
          <p className="text-sm text-gray-500">
            Please try uploading a new template or check if the template ID is
            correct.
          </p>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      className="card p-6"
      initial={{ scale: 0.95, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      transition={{ duration: 0.3 }}
    >
      <h3 className="text-xl font-semibold text-gray-800 mb-4">
        Configure Text Placement
      </h3>

      <div className="space-y-4">
        {/* Mode Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Placement Mode:
          </label>
          <div className="flex space-x-2">
            <button
              onClick={() => setMode("rectangle")}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg border text-sm font-medium transition-all ${
                mode === "rectangle"
                  ? "border-primary-500 bg-primary-50 text-primary-700"
                  : "border-gray-300 bg-white text-gray-700 hover:border-gray-400"
              }`}
            >
              <Square className="w-4 h-4" />
              <span>Rectangle Drawing</span>
            </button>
            <button
              onClick={() => setMode("point")}
              className={`flex items-center space-x-2 px-4 py-2 rounded-lg border text-sm font-medium transition-all ${
                mode === "point"
                  ? "border-primary-500 bg-primary-50 text-primary-700"
                  : "border-gray-300 bg-white text-gray-700 hover:border-gray-400"
              }`}
            >
              <MapPin className="w-4 h-4" />
              <span>Point Click</span>
            </button>
          </div>
        </div>

        {/* Field Type Selection for Rectangle Mode */}
        {mode === "rectangle" && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select field type to draw rectangle for:
            </label>
            <div className="grid grid-cols-3 gap-2">
              <button
                onClick={() => setSelectedType("name")}
                className={`p-2 rounded-lg border text-sm font-medium transition-all ${
                  selectedType === "name"
                    ? "border-blue-500 bg-blue-50 text-blue-700"
                    : "border-gray-300 bg-white text-gray-700 hover:border-gray-400"
                }`}
              >
                STUDENT NAME
              </button>
              <button
                onClick={() => setSelectedType("date")}
                className={`p-2 rounded-lg border text-sm font-medium transition-all ${
                  selectedType === "date"
                    ? "border-green-500 bg-green-50 text-green-700"
                    : "border-gray-300 bg-white text-gray-700 hover:border-gray-400"
                }`}
              >
                DATE
              </button>
              <button
                onClick={() => setSelectedType("certificate_no")}
                className={`p-2 rounded-lg border text-sm font-medium transition-all ${
                  selectedType === "certificate_no"
                    ? "border-yellow-500 bg-yellow-50 text-yellow-700"
                    : "border-gray-300 bg-white text-gray-700 hover:border-gray-400"
                }`}
              >
                CERT NO
              </button>
            </div>
          </div>
        )}

        {/* Placeholder Selection for Point Mode */}
        {mode === "point" && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select placeholder to position:
            </label>
            <div className="grid grid-cols-3 gap-2">
              {placeholders.map((placeholder) => (
                <button
                  key={placeholder.key}
                  onClick={() => setSelectedPlaceholder(placeholder.key)}
                  className={`p-2 rounded-lg border text-sm font-medium transition-all ${
                    selectedPlaceholder === placeholder.key
                      ? "border-primary-500 bg-primary-50 text-primary-700"
                      : "border-gray-300 bg-white text-gray-700 hover:border-gray-400"
                  }`}
                >
                  {placeholder.key.replace("_", " ").toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Template Image */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            {mode === "rectangle"
              ? "Draw rectangles on the image to define text placement areas"
              : "Click on the image to position the selected placeholder"}
            :
          </label>

          {mode === "rectangle" ? (
            <RectangleDrawingCanvas
              imageUrl={template.image_path}
              onRectangleComplete={handleRectangleComplete}
              existingRectangles={rectangles}
              selectedType={selectedType}
              onRectangleUpdate={handleRectangleUpdate}
            />
          ) : (
            <div className="relative border border-gray-300 rounded-lg overflow-hidden">
              {template.image_path ? (
                <GoogleDriveImage
                  src={template.image_path}
                  alt="Template"
                  className="w-full h-auto cursor-crosshair"
                  fallbackComponent={
                    <div className="w-full h-64 bg-gray-100 flex items-center justify-center">
                      <div className="text-center">
                        <div className="text-gray-400 text-4xl mb-2">🖼️</div>
                        <p className="text-gray-500 font-medium">Template</p>
                        <p className="text-sm text-gray-400">
                          Image not available
                        </p>
                        {template.image_path && (
                          <p className="text-xs text-gray-400 mt-1">
                            Path: {template.image_path}
                          </p>
                        )}
                      </div>
                    </div>
                  }
                />
              ) : (
                <div className="w-full h-64 bg-gray-100 flex items-center justify-center">
                  <div className="text-center">
                    <div className="text-gray-400 text-4xl mb-2">🖼️</div>
                    <p className="text-gray-500 font-medium">Template</p>
                    <p className="text-sm text-gray-400">
                      No image path available
                    </p>
                  </div>
                </div>
              )}

              {/* Placeholder markers */}
              {placeholders.map((placeholder) => (
                <div
                  key={placeholder.key}
                  className={`absolute w-4 h-4 rounded-full border-2 transform -translate-x-2 -translate-y-2 ${
                    selectedPlaceholder === placeholder.key
                      ? "border-primary-500 bg-primary-500"
                      : "border-white bg-white shadow-lg"
                  }`}
                  style={{ left: placeholder.x, top: placeholder.y }}
                >
                  <MapPin className="w-3 h-3 text-white" />
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Placeholder Settings */}
        {(selectedPlaceholder || selectedType || rectangles.length > 0) && (
          <motion.div
            className="bg-gray-50 p-4 rounded-lg"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
          >
            <h4 className="font-medium text-gray-800 mb-3">
              {mode === "rectangle"
                ? "Rectangle Drawing Settings"
                : `Settings for ${(selectedPlaceholder || selectedType)
                    ?.replace("_", " ")
                    .toUpperCase()}`}
            </h4>

            {mode === "rectangle" ? (
              <div className="space-y-4">
                {["name", "date", "certificate_no"].map((type) => {
                  const placeholder = placeholders.find(
                    (p) => p.key === (type === "name" ? "student_name" : type)
                  );
                  return (
                    <div
                      key={type}
                      className="border border-gray-200 rounded-lg p-3"
                    >
                      <h5 className="font-medium text-gray-700 mb-2">
                        {type === "name"
                          ? "Student Name"
                          : type.replace("_", " ").toUpperCase()}
                      </h5>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">
                            Font Size
                          </label>
                          <input
                            type="number"
                            value={
                              placeholder?.font_size ||
                              (type === "name" ? 48 : type === "date" ? 18 : 16)
                            }
                            onChange={(e) =>
                              handlePlaceholderChange(
                                type === "name" ? "student_name" : type,
                                "font_size",
                                parseInt(e.target.value)
                              )
                            }
                            className="input-field text-sm"
                            min="12"
                            max="72"
                          />
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">
                            Color
                          </label>
                          <input
                            type="color"
                            value={placeholder?.color || "#0b2a4a"}
                            onChange={(e) =>
                              handlePlaceholderChange(
                                type === "name" ? "student_name" : type,
                                "color",
                                e.target.value
                              )
                            }
                            className="w-full h-8 border border-gray-300 rounded"
                          />
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            ) : (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Font Size
                  </label>
                  <input
                    type="number"
                    value={
                      placeholders.find(
                        (p) => p.key === (selectedPlaceholder || selectedType)
                      )?.font_size || 24
                    }
                    onChange={(e) =>
                      handlePlaceholderChange(
                        selectedPlaceholder || selectedType || "",
                        "font_size",
                        parseInt(e.target.value)
                      )
                    }
                    className="input-field"
                    min="12"
                    max="72"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Color
                  </label>
                  <input
                    type="color"
                    value={
                      placeholders.find(
                        (p) => p.key === (selectedPlaceholder || selectedType)
                      )?.color || "#0b2a4a"
                    }
                    onChange={(e) =>
                      handlePlaceholderChange(
                        selectedPlaceholder || selectedType || "",
                        "color",
                        e.target.value
                      )
                    }
                    className="w-full h-10 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>
            )}

            {mode === "rectangle" && (
              <div className="mt-4 space-y-4">
                {["name", "date", "certificate_no"].map((type) => {
                  const placeholder = placeholders.find(
                    (p) => p.key === (type === "name" ? "student_name" : type)
                  );
                  return (
                    <div
                      key={type}
                      className="border border-gray-200 rounded-lg p-3"
                    >
                      <h5 className="font-medium text-gray-700 mb-2">
                        {type === "name"
                          ? "Student Name"
                          : type.replace("_", " ").toUpperCase()}{" "}
                        Alignment
                      </h5>
                      <div className="grid grid-cols-2 gap-3">
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">
                            Text Alignment
                          </label>
                          <select
                            value={
                              placeholder?.text_align ||
                              (type === "name" ? "center" : "left")
                            }
                            onChange={(e) =>
                              handlePlaceholderChange(
                                type === "name" ? "student_name" : type,
                                "text_align",
                                e.target.value
                              )
                            }
                            className="input-field text-sm"
                          >
                            <option value="left">Left</option>
                            <option value="center">Center</option>
                            <option value="right">Right</option>
                          </select>
                        </div>
                        <div>
                          <label className="block text-xs font-medium text-gray-600 mb-1">
                            Vertical Alignment
                          </label>
                          <select
                            value={placeholder?.vertical_align || "center"}
                            onChange={(e) =>
                              handlePlaceholderChange(
                                type === "name" ? "student_name" : type,
                                "vertical_align",
                                e.target.value
                              )
                            }
                            className="input-field text-sm"
                          >
                            <option value="top">Top</option>
                            <option value="center">Center</option>
                            <option value="bottom">Bottom</option>
                          </select>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </motion.div>
        )}

        {/* Action Buttons */}
        <div className="flex space-x-3">
          <button
            onClick={savePlaceholders}
            disabled={saving}
            className="btn-primary flex items-center space-x-2"
          >
            <Save className="w-4 h-4" />
            <span>{saving ? "Saving..." : "Save Configuration"}</span>
          </button>

          <button
            onClick={resetPlaceholders}
            className="btn-secondary flex items-center space-x-2"
          >
            <RotateCcw className="w-4 h-4" />
            <span>Reset</span>
          </button>
        </div>

        {saved && (
          <motion.div
            className="p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.2 }}
          >
            Configuration saved successfully!
          </motion.div>
        )}
      </div>
    </motion.div>
  );
};

export default TemplatePlaceholderEditor;
