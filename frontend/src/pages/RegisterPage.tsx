import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { register } from "../services/auth";
import ThemeSwitcher from "../components/ThemeSwitcher";
import { useToast } from "../context/ToastContext";
import { parseApiError } from "../utils/parseApiError";

export default function RegisterPage() {
  const navigate = useNavigate();
  const { success, error: toastError } = useToast();
  const [form, setForm]     = useState({ username: "", email: "", password: "" });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await register(form);
      success("Account created! Please sign in.");
      navigate("/login");
    } catch (err: unknown) {
      toastError(parseApiError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-brand-50 to-indigo-100 dark:from-gray-950 dark:to-gray-900 px-4">
      <div className="absolute top-4 right-4">
        <ThemeSwitcher />
      </div>
      <div className="card w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-brand-600 mb-4">
            <span className="text-2xl">🔬</span>
          </div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">DermaVision</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Create your free account</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {[
            { label: "Username", key: "username", type: "text",     placeholder: "your_username" },
            { label: "Email",    key: "email",    type: "email",    placeholder: "you@example.com" },
            { label: "Password", key: "password", type: "password", placeholder: "••••••••" },
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
            {loading ? "Registering…" : "Create account"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-gray-500 dark:text-gray-400">
          Already have an account?{" "}
          <Link to="/login" className="text-brand-600 dark:text-brand-400 font-medium hover:underline">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
