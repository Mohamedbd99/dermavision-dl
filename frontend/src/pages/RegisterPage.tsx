import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { register } from "../services/auth";
import ThemeSwitcher from "../components/ThemeSwitcher";
import LanguageSwitcher from "../components/LanguageSwitcher";
import { useToast } from "../context/ToastContext";
import { parseApiError } from "../utils/parseApiError";
import { useTranslation } from "react-i18next";

export default function RegisterPage() {
  const navigate = useNavigate();
  const { success, error: toastError } = useToast();
  const { t } = useTranslation();
  const [form, setForm]     = useState({ username: "", email: "", password: "" });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await register(form);
      success(t("register.successMsg"));
      navigate("/login");
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
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-brand-600 mb-4">
            <span className="text-2xl">🔬</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t("common.appName")}</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{t("register.subtitle")}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {[
            { label: t("common.username"), key: "username", type: "text",     placeholder: t("register.usernamePlaceholder") },
            { label: t("common.email"),    key: "email",    type: "email",    placeholder: t("register.emailPlaceholder") },
            { label: t("common.password"), key: "password", type: "password", placeholder: t("register.passwordPlaceholder") },
          ].map(({ label, key, type, placeholder }) => (
            <div key={key}>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">{label}</label>
              <input
                type={type}
                required
                className="input-field"
                placeholder={placeholder}
                value={form[key as keyof typeof form]}
                onChange={(e) => setForm({ ...form, [key]: e.target.value })}
              />
            </div>
          ))}

          <button type="submit" disabled={loading} className="btn-primary w-full">
            {loading ? t("register.submitting") : t("register.submit")}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
          {t("register.alreadyHave")}{" "}
          <Link to="/login" className="text-brand-600 dark:text-brand-400 font-medium hover:underline">
            {t("register.signInLink")}
          </Link>
        </p>
      </div>
    </div>
  );
}
