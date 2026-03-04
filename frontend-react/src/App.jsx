import { Navigate, Route, Routes } from "react-router-dom";
import { LegacyPage } from "./components/LegacyPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LegacyPage fileName="index.html" />} />
      <Route path="/login" element={<LegacyPage fileName="login.html" />} />
      <Route path="/signup" element={<LegacyPage fileName="signup.html" />} />
      <Route path="/dashboard" element={<LegacyPage fileName="dashboard.html" />} />
      <Route path="/payment" element={<LegacyPage fileName="payment.html" />} />
      <Route path="/admin" element={<LegacyPage fileName="admin.html" />} />
      <Route path="/super-admin" element={<LegacyPage fileName="super-admin.html" />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
