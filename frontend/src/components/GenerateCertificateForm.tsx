import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  User,
  BookOpen,
  Calendar,
  FileText,
  Download,
  Eye,
} from "lucide-react";
import { generateCertificate, getTemplates } from "../services/api";
import GoogleDriveImage from "./GoogleDriveImage";
import { downloadCertificate } from "../utils/downloadUtils";

const GenerateCertificateForm: React.FC = () => {
  const [templates, setTemplates] = useState<any[]>([]);
  const [formData, setFormData] = useState({
    template_id: "",
    student_name: "",
    course_name: "",
    date_str: new Date().toISOString().split("T")[0],
  });
  const [generating, setGenerating] = useState(false);
  const [generated, setGenerated] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [progressMessage, setProgressMessage] = useState<string>("");

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      console.log(
        "Loading templates from:",
        "https://certificate-tb.onrender.com/api/templates"
      );
      const templatesData = await getTemplates();
      console.log("Templates loaded:", templatesData);
      setTemplates(templatesData.templates || []);
    } catch (error) {
      console.error("Failed to load templates:", error);

      // Type-safe error handling
      if (error && typeof error === "object" && "response" in error) {
        const axiosError = error as any;
        console.error("Error details:", axiosError.response?.data);
        console.error("Error status:", axiosError.response?.status);
      }

      // Set error state for user feedback
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error";
      setError(`Failed to load templates: ${errorMessage}`);
    }
  };

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setGenerating(true);
    setProgressMessage("Starting certificate generation...");

    try {
      setProgressMessage("Generating certificate image...");

      // Detect device type for responsive behavior
      const isMobile = window.innerWidth <= 768;
      const deviceType = isMobile ? "mobile" : "desktop";

      // Add device type to form data for responsive behavior
      const responsiveFormData = {
        ...formData,
        device_type: deviceType,
      };

      const result = await generateCertificate(responsiveFormData);
      setProgressMessage("Certificate generated successfully!");
      setGenerated(result);
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to generate certificate";
      setError(errorMessage);
      setProgressMessage("");
    } finally {
      setGenerating(false);
      setProgressMessage("");
    }
  };

  const resetForm = () => {
    setFormData({
      template_id: "",
      student_name: "",
      course_name: "",
      date_str: new Date().toISOString().split("T")[0],
    });
    setGenerated(null);
    setError(null);
    setProgressMessage("");
  };

  return (
    <div className="max-w-4xl mx-auto">
      <motion.div
        className="card p-8"
        initial={{ scale: 0.95, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ duration: 0.3 }}
      >
        <h3 className="text-2xl font-semibold text-gray-800 mb-6">
          Generate New Certificate
        </h3>

        {!generated ? (
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Template Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <FileText className="w-4 h-4 inline mr-2" />
                Select Template
              </label>
              <div className="flex space-x-2">
                <select
                  name="template_id"
                  value={formData.template_id}
                  onChange={handleInputChange}
                  className="input-field flex-1"
                  required
                >
                  <option value="">Choose a template...</option>
                  {templates.map((template) => (
                    <option
                      key={template.template_id}
                      value={template.template_id}
                    >
                      {template.name}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={loadTemplates}
                  className="btn-secondary px-3 py-2 text-sm"
                  title="Reload templates"
                >
                  🔄
                </button>
              </div>
              {templates.length === 0 && (
                <p className="text-sm text-gray-500 mt-1">
                  No templates found. Try refreshing or upload a new template.
                </p>
              )}
            </div>

            {/* Student Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <User className="w-4 h-4 inline mr-2" />
                Student Name
              </label>
              <input
                type="text"
                name="student_name"
                value={formData.student_name}
                onChange={handleInputChange}
                className="input-field"
                placeholder="Enter student's full name"
                required
              />
            </div>

            {/* Course Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <BookOpen className="w-4 h-4 inline mr-2" />
                Course Name
              </label>
              <input
                type="text"
                name="course_name"
                value={formData.course_name}
                onChange={handleInputChange}
                className="input-field"
                placeholder="Enter course name"
                required
              />
            </div>

            {/* Date */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Calendar className="w-4 h-4 inline mr-2" />
                Date of Registration
              </label>
              <input
                type="date"
                name="date_str"
                value={formData.date_str}
                onChange={handleInputChange}
                className="input-field"
                required
              />
            </div>

            {error && (
              <motion.div
                className="p-4 bg-red-50 border border-red-200 rounded-lg text-red-700"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
              >
                {error}
              </motion.div>
            )}

            {progressMessage && (
              <motion.div
                className="p-4 bg-blue-50 border border-blue-200 rounded-lg text-blue-700"
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.2 }}
              >
                <div className="flex items-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                  <span>{progressMessage}</span>
                </div>
              </motion.div>
            )}

            <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-4">
              <button
                type="submit"
                disabled={generating}
                className="btn-primary flex items-center justify-center space-x-2 w-full sm:w-auto"
              >
                {generating ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    <span>Generating & Uploading to Drive...</span>
                  </>
                ) : (
                  <>
                    <FileText className="w-4 h-4" />
                    <span>Generate Certificate</span>
                  </>
                )}
              </button>
            </div>
          </form>
        ) : (
          <motion.div
            className="text-center"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.4 }}
          >
            <div className="bg-green-50 border border-green-200 rounded-lg p-6 mb-6">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg
                  className="w-8 h-8 text-green-600"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth="2"
                    d="M5 13l4 4L19 7"
                  ></path>
                </svg>
              </div>
              <h4 className="text-xl font-semibold text-green-800 mb-2">
                Certificate Generated Successfully!
              </h4>
              <p className="text-green-700">
                Certificate ID:{" "}
                <span className="font-mono font-bold">
                  {generated.certificate_id}
                </span>
              </p>
            </div>

            <div className="grid md:grid-cols-2 gap-6 mb-6">
              <div className="bg-gray-50 p-4 rounded-lg">
                <h5 className="font-medium text-gray-800 mb-2">
                  Certificate Preview
                </h5>
                <GoogleDriveImage
                  src={generated.certificate_url}
                  alt="Generated Certificate"
                  className="w-full h-auto rounded-lg shadow-md"
                  fallbackComponent={
                    <div className="w-full h-64 bg-gray-100 flex items-center justify-center rounded-lg">
                      <div className="text-center">
                        <div className="text-gray-400 text-4xl mb-2">📄</div>
                        <div className="text-lg text-gray-500">Certificate</div>
                        <div className="text-sm text-gray-400">
                          Image not available
                        </div>
                      </div>
                    </div>
                  }
                />
              </div>

              <div className="bg-gray-50 p-4 rounded-lg">
                <h5 className="font-medium text-gray-800 mb-2">QR Code</h5>
                <GoogleDriveImage
                  src={generated.qr_url}
                  alt="QR Code"
                  className="w-32 h-32 mx-auto rounded-lg shadow-md"
                  fallbackComponent={
                    <div className="w-32 h-32 mx-auto bg-gray-100 flex items-center justify-center rounded-lg">
                      <div className="text-center">
                        <div className="text-gray-400 text-2xl mb-1">📱</div>
                        <div className="text-xs text-gray-500">QR Code</div>
                      </div>
                    </div>
                  }
                />
                <p className="text-sm text-gray-600 mt-2 text-center">
                  Scan to verify certificate
                </p>
              </div>
            </div>

            <div className="flex space-x-4 justify-center">
              <button
                onClick={() =>
                  downloadCertificate(
                    generated.certificate_url,
                    formData.student_name
                  )
                }
                className="btn-primary flex items-center space-x-2"
              >
                <Download className="w-4 h-4" />
                <span>Download Certificate</span>
              </button>

              <a
                href={`https://certificate-tb.onrender.com/verify/${generated.certificate_id}`}
                target="_blank"
                rel="noopener noreferrer"
                className="btn-secondary flex items-center space-x-2"
              >
                <Eye className="w-4 h-4" />
                <span>View Verification Page</span>
              </a>
            </div>

            <button
              onClick={resetForm}
              className="mt-6 text-primary-600 hover:text-primary-700 font-medium"
            >
              Generate Another Certificate
            </button>
          </motion.div>
        )}
      </motion.div>
    </div>
  );
};

export default GenerateCertificateForm;
