import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  FileText,
  Upload,
  Settings,
  Users,
  CheckCircle,
  Download,
  Plus,
  Eye,
} from "lucide-react";
import TemplateUploader from "./TemplateUploader";
import TemplatePlaceholderEditor from "./TemplatePlaceholderEditor";
import GenerateCertificateForm from "./GenerateCertificateForm";
import CertificateList from "./CertificateList";

const AdminDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState("templates");
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);

  const tabs = [
    { id: "templates", label: "Templates", icon: FileText },
    { id: "generate", label: "Generate", icon: Plus },
    { id: "certificates", label: "Certificates", icon: Users },
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-softBg to-blue-50">
      {/* Header */}
      <motion.header
        className="gradient-header shadow-xl"
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6 }}
      >
        <div className="container mx-auto px-6 py-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold text-white mb-2">
                Tech Buddy Space
              </h1>
              <p className="text-blue-100 text-lg">
                Certificate Generation & QR Verification System
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="bg-white/20 rounded-lg px-4 py-2">
                <span className="text-white font-medium">Admin Dashboard</span>
              </div>
            </div>
          </div>
        </div>
      </motion.header>

      {/* Navigation Tabs */}
      <motion.nav
        className="bg-white shadow-lg border-b border-gray-200"
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.6, delay: 0.1 }}
      >
        <div className="container mx-auto px-6">
          <div className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-4 px-2 border-b-2 transition-all duration-200 ${
                    activeTab === tab.id
                      ? "border-primary-500 text-primary-600"
                      : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300"
                  }`}
                >
                  <Icon className="w-5 h-5" />
                  <span className="font-medium">{tab.label}</span>
                </button>
              );
            })}
          </div>
        </div>
      </motion.nav>

      {/* Main Content */}
      <motion.main
        className="container mx-auto px-6 py-8"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.6, delay: 0.2 }}
      >
        {activeTab === "templates" && (
          <div className="space-y-8">
            <motion.div
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ duration: 0.5 }}
            >
              <h2 className="text-3xl font-bold text-gray-800 mb-6">
                Template Management
              </h2>
              <div className="grid lg:grid-cols-2 gap-8">
                <TemplateUploader onTemplateUploaded={setSelectedTemplate} />
                {selectedTemplate && (
                  <TemplatePlaceholderEditor templateId={selectedTemplate} />
                )}
              </div>
            </motion.div>
          </div>
        )}

        {activeTab === "generate" && (
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="text-3xl font-bold text-gray-800 mb-6">
              Generate Certificate
            </h2>
            <GenerateCertificateForm />
          </motion.div>
        )}

        {activeTab === "certificates" && (
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="text-3xl font-bold text-gray-800 mb-6">
              Certificate Management
            </h2>
            <CertificateList />
          </motion.div>
        )}
      </motion.main>
    </div>
  );
};

export default AdminDashboard;
