import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { FileText, Users, Plus } from "lucide-react";
import TemplateUploader from "./TemplateUploader";
import TemplatePlaceholderEditor from "./TemplatePlaceholderEditor";
import GenerateCertificateForm from "./GenerateCertificateForm";
import CertificateList from "./CertificateList";
import { getTemplates } from "../services/api";

const AdminDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState("templates");
  const [selectedTemplate, setSelectedTemplate] = useState<string | null>(null);
  const [templates, setTemplates] = useState<any[]>([]);

  const loadTemplates = async () => {
    try {
      const templatesData = await getTemplates();
      setTemplates(templatesData.templates || []);
    } catch (error) {
      console.error("Failed to load templates:", error);
    }
  };

  useEffect(() => {
    if (activeTab === "templates") {
      loadTemplates();
    }
  }, [activeTab]);

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
              <div className="space-y-8">
                {/* Template List */}
                {templates.length > 0 && (
                  <div>
                    <h3 className="text-xl font-semibold text-gray-800 mb-4">
                      Existing Templates
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                      {templates.map((template) => (
                        <motion.div
                          key={template.template_id}
                          className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
                            selectedTemplate === template.template_id
                              ? "border-blue-500 bg-blue-50"
                              : "border-gray-200 hover:border-gray-300"
                          }`}
                          onClick={() =>
                            setSelectedTemplate(template.template_id)
                          }
                          whileHover={{ scale: 1.02 }}
                          whileTap={{ scale: 0.98 }}
                        >
                          <div className="aspect-video bg-gray-100 rounded-lg mb-3 overflow-hidden">
                            <img
                              src={template.image_path}
                              alt={template.name}
                              className="w-full h-full object-cover"
                              onError={(e) => {
                                e.currentTarget.style.display = "none";
                                e.currentTarget.nextElementSibling?.classList.remove(
                                  "hidden"
                                );
                              }}
                            />
                            <div className="hidden w-full h-full flex items-center justify-center text-gray-400">
                              <div className="text-center">
                                <div className="text-2xl mb-2">🖼️</div>
                                <div className="text-sm">
                                  Image not available
                                </div>
                              </div>
                            </div>
                          </div>
                          <h4 className="font-medium text-gray-800">
                            {template.name}
                          </h4>
                          <p className="text-sm text-gray-500">
                            {template.description}
                          </p>
                          <p className="text-xs text-gray-400 mt-1">
                            ID: {template.template_id}
                          </p>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Upload New Template */}
                <div>
                  <h3 className="text-xl font-semibold text-gray-800 mb-4">
                    Upload New Template
                  </h3>
                  <TemplateUploader
                    onTemplateUploaded={(templateId) => {
                      setSelectedTemplate(templateId);
                      loadTemplates(); // Reload templates list
                    }}
                  />
                </div>

                {/* Template Editor */}
                {selectedTemplate && (
                  <div>
                    <h3 className="text-xl font-semibold text-gray-800 mb-4">
                      Configure Template
                    </h3>
                    <TemplatePlaceholderEditor templateId={selectedTemplate} />
                  </div>
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
