import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import AdminDashboard from "./components/AdminDashboard";
import PublicVerifyPage from "./components/PublicVerifyPage";
import LoginPage from "./components/LoginPage";
import ProtectedRoute from "./components/ProtectedRoute";
import "./index.css";

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-softBg to-blue-50">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <AdminDashboard />
              </ProtectedRoute>
            }
          />
          <Route path="/verify/:certificateId" element={<PublicVerifyPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
