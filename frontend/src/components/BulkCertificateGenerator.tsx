import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Upload,
  Download,
  Users,
  CheckCircle,
  XCircle,
  AlertCircle,
} from "lucide-react";
import { getTemplates, bulkGenerateCertificates } from "../services/api";
import { downloadCSV } from "../utils/downloadUtils";

interface BulkResult {
  row: number;
  student_name: string;
  course_name: string;
  date_str: string;
  certificate_id: string;
  certificate_url: string;
  qr_url: string;
  status: string;
}

interface BulkError {
  row: number;
  student_name: string;
  error: string;
  status: string;
}

interface BulkResponse {
  message: string;
  total_students: number;
  successful: number;
  failed: number;
  results: BulkResult[];
  errors: BulkError[];
}

const BulkCertificateGenerator: React.FC = () => {
  const [templates, setTemplates] = useState<any[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState<string>("");
  const [csvFile, setCsvFile] = useState<File | null>(null);
  const [deviceType, setDeviceType] = useState<string>("desktop");
  const [isGenerating, setIsGenerating] = useState(false);
  const [bulkResult, setBulkResult] = useState<BulkResponse | null>(null);
  const [csvPreview, setCsvPreview] = useState<any[]>([]);
  const [error, setError] = useState<string>("");
  const [progressMessage, setProgressMessage] = useState<string>("");

  // Load templates on component mount
  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      const response = await getTemplates();
      setTemplates(response.templates || []);
    } catch (error) {
      console.error("Failed to load templates:", error);
      setError("Failed to load templates");
    }
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (!file.name.endsWith(".csv")) {
        setError("Please select a CSV file");
        return;
      }
      setCsvFile(file);
      setError("");
      previewCsvFile(file);
    }
  };

  const previewCsvFile = (file: File) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      const text = e.target?.result as string;
      const lines = text.split("\n");
      const headers = lines[0].split(",").map((h) => h.trim());
      const preview = lines.slice(1, 6).map((line) => {
        const values = line.split(",").map((v) => v.trim());
        const row: any = {};
        headers.forEach((header, index) => {
          row[header] = values[index] || "";
        });
        return row;
      });
      setCsvPreview(preview);
    };
    reader.readAsText(file);
  };

  const downloadSampleCsv = () => {
    const sampleData = [
      {
        student_name: "John Doe",
        course_name: "Web Development",
        date_str: "2025-01-15",
      },
      {
        student_name: "Jane Smith",
        course_name: "Data Science",
        date_str: "2025-01-15",
      },
      {
        student_name: "Bob Johnson",
        course_name: "Mobile App Development",
        date_str: "2025-01-15",
      },
    ];

    const csvContent = [
      "student_name,course_name,date_str",
      ...sampleData.map(
        (row) => `${row.student_name},${row.course_name},${row.date_str}`
      ),
    ].join("\n");

    downloadCSV(csvContent, "sample_students.csv");
  };

  const handleBulkGenerate = async () => {
    if (!selectedTemplate) {
      setError("Please select a template");
      return;
    }
    if (!csvFile) {
      setError("Please select a CSV file");
      return;
    }

    setIsGenerating(true);
    setError("");
    setBulkResult(null);
    setProgressMessage("Starting bulk generation...");

    try {
      // Show progress message
      setProgressMessage(
        "Processing CSV file and generating certificates. This may take a few minutes for large files..."
      );

      const result = await bulkGenerateCertificates(
        selectedTemplate,
        csvFile,
        deviceType
      );
      setBulkResult(result);
      setProgressMessage("");
    } catch (error: any) {
      console.error("Bulk generation error:", error);
      if (error.code === "ECONNABORTED" || error.message.includes("timeout")) {
        setError(
          "Request timed out. The bulk generation is taking longer than expected. Please try with a smaller CSV file or try again."
        );
      } else {
        setError(
          error.response?.data?.detail || "Failed to generate certificates"
        );
      }
      setProgressMessage("");
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadResultsCsv = () => {
    if (!bulkResult) return;

    const csvContent = [
      "student_name,course_name,date_str,certificate_id,certificate_url,qr_url,status",
      ...bulkResult.results.map(
        (result) =>
          `${result.student_name},${result.course_name},${result.date_str},${result.certificate_id},${result.certificate_url},${result.qr_url},${result.status}`
      ),
      ...bulkResult.errors.map(
        (error) => `${error.student_name},,,,,"${error.error}",${error.status}`
      ),
    ].join("\n");

    const filename = `bulk_certificates_${
      new Date().toISOString().split("T")[0]
    }.csv`;
    downloadCSV(csvContent, filename);
  };

  return (
    <div className="space-y-6">
      <motion.div
        className="card p-6"
        initial={{ y: 20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        <h3 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
          <Users className="w-5 h-5 mr-2 text-primary-600" />
          Bulk Certificate Generation
        </h3>

        <div className="space-y-4">
          {/* Template Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Template
            </label>
            <select
              value={selectedTemplate}
              onChange={(e) => setSelectedTemplate(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="">Choose a template...</option>
              {templates.map((template) => (
                <option key={template.template_id} value={template.template_id}>
                  {template.name}
                </option>
              ))}
            </select>
          </div>

          {/* Device Type Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Device Type
            </label>
            <select
              value={deviceType}
              onChange={(e) => setDeviceType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="desktop">Desktop</option>
              <option value="mobile">Mobile</option>
            </select>
          </div>

          {/* CSV File Upload */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Upload CSV File
            </label>
            <div className="flex items-center space-x-4">
              <input
                type="file"
                accept=".csv"
                onChange={handleFileUpload}
                className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-primary-50 file:text-primary-700 hover:file:bg-primary-100"
              />
              <button
                onClick={downloadSampleCsv}
                className="flex items-center px-3 py-2 text-sm text-primary-600 hover:text-primary-800 border border-primary-300 rounded-lg hover:bg-primary-50"
              >
                <Download className="w-4 h-4 mr-1" />
                Sample CSV
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-1">
              Required columns: student_name, date_str. Optional: course_name
            </p>
          </div>

          {/* CSV Preview */}
          {csvPreview.length > 0 && (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                CSV Preview (First 5 rows)
              </label>
              <div className="overflow-x-auto border border-gray-200 rounded-lg">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      {Object.keys(csvPreview[0] || {}).map((header) => (
                        <th
                          key={header}
                          className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase"
                        >
                          {header}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {csvPreview.map((row, index) => (
                      <tr key={index}>
                        {Object.values(row).map((value: any, cellIndex) => (
                          <td
                            key={cellIndex}
                            className="px-3 py-2 text-sm text-gray-900"
                          >
                            {value}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <div className="flex items-center">
                <XCircle className="w-4 h-4 text-red-500 mr-2" />
                <span className="text-sm text-red-700">{error}</span>
              </div>
            </div>
          )}

          {/* Progress Message */}
          {progressMessage && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500 mr-2"></div>
                <span className="text-sm text-blue-700">{progressMessage}</span>
              </div>
            </div>
          )}

          {/* Generate Button */}
          <button
            onClick={handleBulkGenerate}
            disabled={!selectedTemplate || !csvFile || isGenerating}
            className="w-full bg-primary-600 hover:bg-primary-700 disabled:bg-gray-400 text-white px-4 py-2 rounded-lg flex items-center justify-center space-x-2 transition-colors duration-200"
          >
            {isGenerating ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Generating Certificates...</span>
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                <span>Generate Certificates</span>
              </>
            )}
          </button>
        </div>
      </motion.div>

      {/* Results Display */}
      {bulkResult && (
        <motion.div
          className="card p-6"
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-xl font-semibold text-gray-800 flex items-center">
              <CheckCircle className="w-5 h-5 mr-2 text-green-600" />
              Generation Results
            </h3>
            <button
              onClick={downloadResultsCsv}
              className="flex items-center px-3 py-2 text-sm text-primary-600 hover:text-primary-800 border border-primary-300 rounded-lg hover:bg-primary-50"
            >
              <Download className="w-4 h-4 mr-1" />
              Download Results
            </button>
          </div>

          {/* Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="text-2xl font-bold text-blue-600">
                {bulkResult.total_students}
              </div>
              <div className="text-sm text-blue-700">Total Students</div>
            </div>
            <div className="bg-green-50 border border-green-200 rounded-lg p-4">
              <div className="text-2xl font-bold text-green-600">
                {bulkResult.successful}
              </div>
              <div className="text-sm text-green-700">Successful</div>
            </div>
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="text-2xl font-bold text-red-600">
                {bulkResult.failed}
              </div>
              <div className="text-sm text-red-700">Failed</div>
            </div>
          </div>

          {/* Detailed Results */}
          <div className="space-y-4">
            {bulkResult.results.length > 0 && (
              <div>
                <h4 className="text-lg font-medium text-gray-800 mb-3">
                  Successful Certificates
                </h4>
                <div className="overflow-x-auto border border-gray-200 rounded-lg">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          Student
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          Course
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          Date
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          Certificate ID
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          Actions
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {bulkResult.results.map((result, index) => (
                        <tr key={index}>
                          <td className="px-3 py-2 text-sm text-gray-900">
                            {result.student_name}
                          </td>
                          <td className="px-3 py-2 text-sm text-gray-900">
                            {result.course_name}
                          </td>
                          <td className="px-3 py-2 text-sm text-gray-900">
                            {result.date_str}
                          </td>
                          <td className="px-3 py-2 text-sm text-gray-900 font-mono">
                            {result.certificate_id}
                          </td>
                          <td className="px-3 py-2 text-sm text-gray-900">
                            <div className="flex space-x-2">
                              <a
                                href={result.certificate_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-primary-600 hover:text-primary-800"
                              >
                                View Certificate
                              </a>
                              <a
                                href={result.qr_url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-green-600 hover:text-green-800"
                              >
                                View QR
                              </a>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {bulkResult.errors.length > 0 && (
              <div>
                <h4 className="text-lg font-medium text-gray-800 mb-3 flex items-center">
                  <AlertCircle className="w-4 h-4 mr-2 text-red-500" />
                  Errors
                </h4>
                <div className="overflow-x-auto border border-gray-200 rounded-lg">
                  <table className="min-w-full divide-y divide-gray-200">
                    <thead className="bg-gray-50">
                      <tr>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          Row
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          Student
                        </th>
                        <th className="px-3 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                          Error
                        </th>
                      </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-gray-200">
                      {bulkResult.errors.map((error, index) => (
                        <tr key={index}>
                          <td className="px-3 py-2 text-sm text-gray-900">
                            {error.row}
                          </td>
                          <td className="px-3 py-2 text-sm text-gray-900">
                            {error.student_name}
                          </td>
                          <td className="px-3 py-2 text-sm text-red-600">
                            {error.error}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        </motion.div>
      )}
    </div>
  );
};

export default BulkCertificateGenerator;
