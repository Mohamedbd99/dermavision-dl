import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute, { GuestRoute } from "./router/ProtectedRoute";
import LoginPage    from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import PredictPage  from "./pages/PredictPage";
import DashboardPage from "./pages/DashboardPage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route element={<GuestRoute />}>
            <Route path="/login"    element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
          </Route>

          {/* Protected routes */}
          <Route element={<ProtectedRoute />}>
            <Route path="/predict"   element={<PredictPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
          </Route>

          {/* Default redirect */}
          <Route path="*" element={<Navigate to="/predict" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
