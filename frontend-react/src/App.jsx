import { NavLink, Navigate, Route, Routes } from "react-router-dom";
import { LegacyParityPage } from "./components/LegacyParityPage";
import { LandingPage } from "./pages/LandingPage";

const routes = [
  { to: "/", label: "Landing" },
  { to: "/login", label: "Login" },
  { to: "/signup", label: "Signup" },
  { to: "/dashboard", label: "Dashboard" },
  { to: "/payment", label: "Payment" },
  { to: "/admin", label: "Admin" },
  { to: "/super-admin", label: "Super Admin" }
];

export default function App() {
  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="container topbar-inner">
          <div className="brand">Anexi<span>.ai</span></div>
          <nav className="topbar-nav">
            {routes.map((route) => (
              <NavLink
                key={route.to}
                to={route.to}
                className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
                end={route.to === "/"}
              >
                {route.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </header>

      <main>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LegacyParityPage pageName="Login" source="frontend/login.html" />} />
          <Route path="/signup" element={<LegacyParityPage pageName="Signup" source="frontend/signup.html" />} />
          <Route path="/dashboard" element={<LegacyParityPage pageName="Dashboard" source="frontend/dashboard.html" />} />
          <Route path="/payment" element={<LegacyParityPage pageName="Payment" source="frontend/payment.html" />} />
          <Route path="/admin" element={<LegacyParityPage pageName="Admin" source="frontend/admin.html" />} />
          <Route path="/super-admin" element={<LegacyParityPage pageName="Super Admin" source="frontend/super-admin.html" />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>
    </div>
  );
}
