import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { useParams } from "react-router-dom";
import {
  CheckCircle,
  XCircle,
  Download,
  User,
  FileText,
  AlertTriangle,
} from "lucide-react";
import { getCertificate, downloadCertificateDirect } from "../services/api";
import GoogleDriveImage from "./GoogleDriveImage";

const PublicVerifyPage: React.FC = () => {
  const { certificateId } = useParams<{ certificateId: string }>();
  const [certificate, setCertificate] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (certificateId) {
      loadCertificate();
    }
  }, [certificateId]);

  const loadCertificate = async () => {
    try {
      setLoading(true);
      const cert = await getCertificate(certificateId!);
      if (cert) {
        setCertificate(cert);
      } else {
        setError("Certificate not found");
      }
    } catch (err) {
      setError("Failed to load certificate");
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-softBg to-blue-50 flex items-center justify-center">
        <motion.div
          className="text-center"
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">Verifying certificate...</p>
        </motion.div>
      </div>
    );
  }

  if (error || !certificate) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-softBg to-blue-50 flex items-center justify-center">
        <motion.div
          className="max-w-md mx-auto text-center"
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <div className="bg-white rounded-xl shadow-2xl p-8">
            <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <XCircle className="w-10 h-10 text-red-600" />
            </div>
            <h1 className="text-2xl font-bold text-gray-800 mb-4">
              Certificate Not Found
            </h1>
            <p className="text-gray-600 mb-6">
              The certificate you're looking for doesn't exist or has been
              revoked.
            </p>
            <div className="bg-gray-50 rounded-lg p-4">
              <p className="text-sm text-gray-500 font-mono">
                Certificate ID: {certificateId}
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    );
  }

  const isVerified = certificate.verified && !certificate.revoked;

  return (
    <div className="min-h-screen bg-gradient-to-br from-softBg to-blue-50">
      <div className="container mx-auto px-4 py-8">
        <motion.div
          className="max-w-4xl mx-auto"
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.6 }}
        >
          <div className="bg-white rounded-xl shadow-2xl overflow-hidden">
            {/* Header */}
            <div className="gradient-header p-8 text-center">
              <motion.div
                className="mb-6"
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                transition={{ duration: 0.5, delay: 0.2 }}
              >
                {isVerified ? (
                  <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <motion.div
                      animate={{
                        scale: [1, 1.1, 1],
                        rotate: [0, 5, -5, 0],
                      }}
                      transition={{
                        duration: 0.6,
                        repeat: Infinity,
                        repeatDelay: 2,
                      }}
                    >
                      <CheckCircle className="w-10 h-10 text-green-600" />
                    </motion.div>
                  </div>
                ) : (
                  <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
                    <XCircle className="w-10 h-10 text-red-600" />
                  </div>
                )}
              </motion.div>

              <h1 className="text-4xl font-bold text-white mb-2">
                Certificate Verification
              </h1>
              <p className="text-blue-100 text-lg">Tech Buddy Space</p>
            </div>

            {/* Status Banner */}
            <motion.div
              className={`p-6 ${isVerified ? "bg-green-50" : "bg-red-50"}`}
              initial={{ y: -20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ duration: 0.5, delay: 0.3 }}
            >
              <div className="flex items-center justify-center">
                {isVerified ? (
                  <div className="flex items-center text-green-800">
                    <CheckCircle className="w-6 h-6 mr-2" />
                    <span className="text-xl font-semibold">
                      Certificate Verified Successfully
                    </span>
                  </div>
                ) : (
                  <div className="flex items-center text-red-800">
                    <XCircle className="w-6 h-6 mr-2" />
                    <span className="text-xl font-semibold">
                      Certificate Revoked
                    </span>
                  </div>
                )}
              </div>
            </motion.div>

            {/* Content */}
            <div className="p-8">
              <div className="grid lg:grid-cols-2 gap-8">
                {/* Certificate Details */}
                <motion.div
                  className="space-y-6"
                  initial={{ x: -20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ duration: 0.5, delay: 0.4 }}
                >
                  <div className="bg-gray-50 rounded-lg p-6">
                    <h3 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
                      <User className="w-5 h-5 mr-2" />
                      Student Information
                    </h3>
                    <div className="space-y-3">
                      <div>
                        <span className="text-sm font-medium text-gray-600">
                          Name:
                        </span>
                        <p className="text-lg font-semibold text-gray-800">
                          {certificate.student_name}
                        </p>
                      </div>
                      <div>
                        <span className="text-sm font-medium text-gray-600">
                          Course:
                        </span>
                        <p className="text-lg font-semibold text-gray-800">
                          {certificate.course_name}
                        </p>
                      </div>
                      <div>
                        <span className="text-sm font-medium text-gray-600">
                          Date:
                        </span>
                        <p className="text-lg font-semibold text-gray-800">
                          {certificate.date_of_registration}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-gray-50 rounded-lg p-6">
                    <h3 className="text-xl font-semibold text-gray-800 mb-4 flex items-center">
                      <FileText className="w-5 h-5 mr-2" />
                      Certificate Details
                    </h3>
                    <div className="space-y-3">
                      <div>
                        <span className="text-sm font-medium text-gray-600">
                          Certificate ID:
                        </span>
                        <p className="text-lg font-mono font-semibold text-gray-800">
                          {certificate.certificate_id}
                        </p>
                      </div>
                      <div>
                        <span className="text-sm font-medium text-gray-600">
                          Issued:
                        </span>
                        <p className="text-lg font-semibold text-gray-800">
                          {formatDate(certificate.issued_at)}
                        </p>
                      </div>
                      <div>
                        <span className="text-sm font-medium text-gray-600">
                          Status:
                        </span>
                        <p
                          className={`text-lg font-semibold ${
                            isVerified ? "text-green-600" : "text-red-600"
                          }`}
                        >
                          {isVerified ? "Verified" : "Revoked"}
                        </p>
                      </div>
                    </div>
                  </div>

                  {certificate.revoked && certificate.revoked_reason && (
                    <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                      <div className="flex items-start">
                        <AlertTriangle className="w-5 h-5 text-red-600 mr-2 mt-0.5" />
                        <div>
                          <h4 className="font-medium text-red-800">
                            Revocation Reason:
                          </h4>
                          <p className="text-red-700 text-sm mt-1">
                            {certificate.revoked_reason}
                          </p>
                        </div>
                      </div>
                    </div>
                  )}
                </motion.div>

                {/* Certificate Preview */}
                <motion.div
                  className="space-y-6"
                  initial={{ x: 20, opacity: 0 }}
                  animate={{ x: 0, opacity: 1 }}
                  transition={{ duration: 0.5, delay: 0.5 }}
                >
                  <div className="bg-gray-50 rounded-lg p-6">
                    <h3 className="text-xl font-semibold text-gray-800 mb-4">
                      Certificate Preview
                    </h3>
                    <div className="border border-gray-200 rounded-lg overflow-hidden">
                      <GoogleDriveImage
                        src={certificate.image_path}
                        alt="Certificate"
                        className="w-full h-auto"
                        fallbackComponent={
                          <div className="w-full h-64 bg-gray-100 flex items-center justify-center">
                            <div className="text-center">
                              <div className="text-gray-400 text-4xl mb-2">
                                📄
                              </div>
                              <div className="text-lg text-gray-500">
                                Certificate
                              </div>
                              <div className="text-sm text-gray-400">
                                Image not available
                              </div>
                            </div>
                          </div>
                        }
                      />
                    </div>
                  </div>

                  <div className="text-center">
                    <button
                      onClick={() => {
                        console.log("🔽 Download button clicked!");
                        console.log("📄 Certificate data:", {
                          certificate_id: certificate.certificate_id,
                          student_name: certificate.student_name,
                        });
                        downloadCertificateDirect(certificate.certificate_id);
                      }}
                      className="btn-primary inline-flex items-center space-x-2"
                    >
                      <Download className="w-4 h-4" />
                      <span>Download Certificate</span>
                    </button>
                  </div>
                </motion.div>
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};

export default PublicVerifyPage;
