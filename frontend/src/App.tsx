import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { ThemeProvider } from "./context/ThemeContext";
import ProtectedRoute, { GuestRoute } from "./router/ProtectedRoute";
import SidebarLayout from "./components/SidebarLayout";
import { ToastProvider } from "./context/ToastContext";
import LoginPage    from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import PredictPage  from "./pages/PredictPage";
import DashboardPage from "./pages/DashboardPage";
import LandingPage from "./pages/LandingPage";

export default function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            {/* Landing - public */}
            <Route path="/" element={<LandingPage />} />

            {/* Auth-only routes (redirect to /predict if already logged in) */}
            <Route element={<GuestRoute />}>
              <Route path="/login"    element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
            </Route>

            {/* Protected routes wrapped in sidebar layout */}
            <Route element={<ProtectedRoute />}>
              <Route element={<SidebarLayout />}>
                <Route path="/predict"   element={<PredictPage />} />
                <Route path="/dashboard" element={<DashboardPage />} />
              </Route>
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
      </ToastProvider>
    </ThemeProvider>
  );
}
