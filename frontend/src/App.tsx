import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import AdminDashboard from "./components/AdminDashboard";
import PublicVerifyPage from "./components/PublicVerifyPage";
import "./index.css";

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-gradient-to-br from-softBg to-blue-50">
        <Routes>
          <Route path="/" element={<AdminDashboard />} />
          <Route path="/verify/:certificateId" element={<PublicVerifyPage />} />
        </Routes>
      </div>
    </Router>
  );
}

export default App;
