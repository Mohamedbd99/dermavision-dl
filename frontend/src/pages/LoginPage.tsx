import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { login } from "../services/auth";
import { useAuth } from "../context/AuthContext";
import ThemeSwitcher from "../components/ThemeSwitcher";
import LanguageSwitcher from "../components/LanguageSwitcher";
import { useToast } from "../context/ToastContext";
import { parseApiError } from "../utils/parseApiError";
import { useTranslation } from "react-i18next";

export default function LoginPage() {
  const navigate = useNavigate();
  const { refreshUser } = useAuth();
  const { success, error: toastError } = useToast();
  const { t } = useTranslation();

  const [form, setForm]     = useState({ username: "", password: "" });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(form);
      await refreshUser();
      success(t("login.successMsg"));
      navigate("/predict");
    } catch (err: unknown) {
      toastError(parseApiError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-50 to-indigo-100 dark:from-gray-950 dark:to-gray-900 px-4">
      <div className="absolute top-4 end-4 flex items-center gap-2">
        <LanguageSwitcher />
        <ThemeSwitcher />
      </div>
      <div className="card w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-brand-600 mb-4">
            <span className="text-2xl">🔬</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t("common.appName")}</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{t("login.subtitle")}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t("common.username")}
            </label>
            <input
              type="text"
              required
              className="input-field"
              placeholder="your_username"
              value={form.username}
              onChange={(e) => setForm({ ...form, username: e.target.value })}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
              {t("common.password")}
            </label>
            <input
              type="password"
              required
              className="input-field"
              placeholder="••••••••"
              value={form.password}
              onChange={(e) => setForm({ ...form, password: e.target.value })}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="btn-primary w-full"
          >
            {loading ? t("login.submitting") : t("login.submit")}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
          {t("login.noAccount")}{" "}
          <Link to="/register" className="text-brand-600 dark:text-brand-400 font-medium hover:underline">
            {t("login.registerLink")}
          </Link>
        </p>
      </div>
    </div>
  );
}
