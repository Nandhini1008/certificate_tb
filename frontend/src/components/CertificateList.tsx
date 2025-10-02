import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Search,
  Download,
  Eye,
  Trash2,
  CheckCircle,
  XCircle,
  Calendar,
  FileText,
} from "lucide-react";
import {
  getCertificates,
  revokeCertificate,
  deleteCertificate,
  downloadCertificateDirect,
} from "../services/api";
import GoogleDriveImage from "./GoogleDriveImage";

const CertificateList: React.FC = () => {
  const [certificates, setCertificates] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState("");
  const [filterStatus, setFilterStatus] = useState("all");
  const [revoking, setRevoking] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  useEffect(() => {
    loadCertificates();
  }, []);

  const loadCertificates = async () => {
    try {
      setLoading(true);
      const response = await getCertificates();
      setCertificates(response.certificates || []);
    } catch (error) {
      console.error("Failed to load certificates:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleRevoke = async (certificateId: string) => {
    if (!confirm("Are you sure you want to revoke this certificate?")) {
      return;
    }

    try {
      setRevoking(certificateId);
      await revokeCertificate(certificateId, "Revoked by admin");
      await loadCertificates(); // Reload the list
    } catch (error) {
      console.error("Failed to revoke certificate:", error);
      alert("Failed to revoke certificate");
    } finally {
      setRevoking(null);
    }
  };

  const handleDelete = async (certificateId: string) => {
    if (
      !confirm(
        "Are you sure you want to permanently delete this certificate? This action cannot be undone."
      )
    ) {
      return;
    }

    try {
      setDeleting(certificateId);
      await deleteCertificate(certificateId);
      // Remove from UI immediately without reloading
      setCertificates((prev) =>
        prev.filter((cert) => cert.certificate_id !== certificateId)
      );
    } catch (error) {
      console.error("Failed to delete certificate:", error);
      alert("Failed to delete certificate");
    } finally {
      setDeleting(null);
    }
  };

  const filteredCertificates = certificates.filter((cert) => {
    const matchesSearch =
      cert.student_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (cert.course_name &&
        cert.course_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      cert.certificate_id.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesFilter =
      filterStatus === "all" ||
      (filterStatus === "verified" &&
        cert.verified === true &&
        cert.revoked !== true) ||
      (filterStatus === "revoked" && cert.revoked === true);

    return matchesSearch && matchesFilter;
  });

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  if (loading) {
    return (
      <motion.div
        className="card p-8"
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

  return (
    <motion.div
      className="space-y-6"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      {/* Search and Filter */}
      <div className="card p-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
              <input
                type="text"
                placeholder="Search certificates..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="input-field pl-10"
              />
            </div>
          </div>

          <div className="md:w-48">
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="input-field"
            >
              <option value="all">All Certificates</option>
              <option value="verified">Verified</option>
              <option value="revoked">Revoked</option>
            </select>
          </div>
        </div>
      </div>

      {/* Certificates Grid */}
      <div className="grid gap-6">
        {filteredCertificates.length === 0 ? (
          <motion.div
            className="card p-8 text-center"
            initial={{ scale: 0.95, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.3 }}
          >
            <div className="text-gray-400 mb-4">
              <FileText className="w-16 h-16 mx-auto" />
            </div>
            <h3 className="text-lg font-medium text-gray-600 mb-2">
              {searchTerm || filterStatus !== "all"
                ? "No certificates match your search"
                : "No certificates found"}
            </h3>
            <p className="text-gray-500">
              {searchTerm || filterStatus !== "all"
                ? "Try adjusting your search or filter criteria"
                : "Generate your first certificate to get started"}
            </p>
          </motion.div>
        ) : (
          filteredCertificates.map((certificate) => (
            <motion.div
              key={certificate.certificate_id}
              className="card p-6"
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ duration: 0.3 }}
            >
              <div className="flex flex-col lg:flex-row gap-6">
                {/* Certificate Preview */}
                <div className="lg:w-1/3">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <GoogleDriveImage
                      src={certificate.image_path}
                      alt="Certificate"
                      className="w-full h-48 object-contain rounded-lg"
                      fallbackComponent={
                        <div className="w-full h-48 bg-gray-100 flex items-center justify-center rounded-lg">
                          <div className="text-center">
                            <div className="text-gray-400 text-2xl mb-2">
                              📄
                            </div>
                            <div className="text-sm text-gray-500">
                              Certificate
                            </div>
                            <div className="text-xs text-gray-400">
                              Image not available
                            </div>
                          </div>
                        </div>
                      }
                    />
                  </div>
                </div>

                {/* Certificate Details */}
                <div className="lg:w-2/3">
                  <div className="flex items-start justify-between mb-4">
                    <div>
                      <h3 className="text-xl font-semibold text-gray-800 mb-1">
                        {certificate.student_name}
                      </h3>
                      <p className="text-gray-600 font-medium">
                        {certificate.course_name}
                      </p>
                      <p className="text-sm text-gray-500 font-mono">
                        {certificate.certificate_id}
                      </p>
                    </div>

                    <div className="flex items-center space-x-2">
                      {certificate.verified && !certificate.revoked ? (
                        <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-green-100 text-green-800">
                          <CheckCircle className="w-4 h-4 mr-1" />
                          Verified
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-red-100 text-red-800">
                          <XCircle className="w-4 h-4 mr-1" />
                          Revoked
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="grid md:grid-cols-2 gap-4 mb-6">
                    <div className="flex items-center text-gray-600">
                      <Calendar className="w-4 h-4 mr-2" />
                      <span className="text-sm">
                        Issued: {formatDate(certificate.issued_at)}
                      </span>
                    </div>

                    <div className="flex items-center text-gray-600">
                      <Calendar className="w-4 h-4 mr-2" />
                      <span className="text-sm">
                        Course Date: {certificate.date_of_registration}
                      </span>
                    </div>
                  </div>

                  {/* Action Buttons */}
                  <div className="flex flex-wrap gap-3">
                    {/* Only show download and verification for non-revoked certificates */}
                    {!certificate.revoked && (
                      <>
                        <button
                          onClick={() =>
                            downloadCertificateDirect(
                              certificate.certificate_id
                            )
                          }
                          className="btn-secondary flex items-center space-x-2"
                        >
                          <Download className="w-4 h-4" />
                          <span>Download</span>
                        </button>

                        <a
                          href={`https://certificate-tb.onrender.com/verify/${certificate.certificate_id}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn-secondary flex items-center space-x-2"
                        >
                          <Eye className="w-4 h-4" />
                          <span>View Verification</span>
                        </a>
                      </>
                    )}

                    {/* Show revoke and delete buttons only for verified, non-revoked certificates */}
                    {certificate.verified && !certificate.revoked && (
                      <>
                        <button
                          onClick={() =>
                            handleRevoke(certificate.certificate_id)
                          }
                          disabled={revoking === certificate.certificate_id}
                          className="bg-orange-600 text-white px-4 py-2 rounded-lg hover:bg-orange-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
                        >
                          {revoking === certificate.certificate_id ? (
                            <>
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                              <span>Revoking...</span>
                            </>
                          ) : (
                            <>
                              <XCircle className="w-4 h-4" />
                              <span>Revoke</span>
                            </>
                          )}
                        </button>

                        <button
                          onClick={() =>
                            handleDelete(certificate.certificate_id)
                          }
                          disabled={deleting === certificate.certificate_id}
                          className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
                        >
                          {deleting === certificate.certificate_id ? (
                            <>
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                              <span>Deleting...</span>
                            </>
                          ) : (
                            <>
                              <Trash2 className="w-4 h-4" />
                              <span>Delete</span>
                            </>
                          )}
                        </button>
                      </>
                    )}

                    {/* Show delete button for revoked certificates */}
                    {certificate.revoked && (
                      <button
                        onClick={() => handleDelete(certificate.certificate_id)}
                        disabled={deleting === certificate.certificate_id}
                        className="bg-red-600 text-white px-4 py-2 rounded-lg hover:bg-red-700 transition-colors flex items-center space-x-2 disabled:opacity-50"
                      >
                        {deleting === certificate.certificate_id ? (
                          <>
                            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                            <span>Deleting...</span>
                          </>
                        ) : (
                          <>
                            <Trash2 className="w-4 h-4" />
                            <span>Delete</span>
                          </>
                        )}
                      </button>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          ))
        )}
      </div>
    </motion.div>
  );
};

export default CertificateList;
