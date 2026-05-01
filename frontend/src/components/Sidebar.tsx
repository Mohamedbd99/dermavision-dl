import React, { useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useAuth } from "../context/AuthContext";
import ThemeSwitcher from "./ThemeSwitcher";
import LanguageSwitcher from "./LanguageSwitcher";

function SidebarContent({ onClose }: { onClose?: () => void }) {
  const { logout, user } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();

  const NAV = [
    { to: "/predict",   icon: "🔬", label: t("common.analyse")   },
    { to: "/dashboard", icon: "📊", label: t("common.dashboard") },
  ];

  const handleLogout = () => { logout(); navigate("/login"); };

  return (
    <div className="flex flex-col h-full py-5">
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 mb-8">
        <div className="w-9 h-9 rounded-xl bg-brand-600 flex items-center justify-center text-base shrink-0">
          🔬
        </div>
        <div className="min-w-0">
          <p className="font-bold text-gray-900 dark:text-white leading-tight">{t("common.appName")}</p>
          <p className="text-xs text-gray-400 dark:text-gray-500 truncate">{user?.username}</p>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 space-y-1">
        <p className="text-[11px] font-semibold text-gray-400 dark:text-gray-500 uppercase tracking-wider px-3 mb-2">
          {t("sidebar.app")}
        </p>
        {NAV.map(({ to, icon, label }) => (
          <NavLink
            key={to}
            to={to}
            onClick={onClose}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
              ${isActive
                ? "bg-brand-50 dark:bg-brand-900/30 text-brand-700 dark:text-brand-300"
                : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700/50 hover:text-gray-900 dark:hover:text-white"
              }`
            }
          >
            <span className="text-base w-5 text-center shrink-0">{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>

      {/* Bottom */}
      <div className="px-3 space-y-1 pt-4 border-t border-gray-200 dark:border-gray-700">
        <NavLink
          to="/"
          onClick={onClose}
          className={({ isActive }) =>
            `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors
            ${isActive
              ? "bg-brand-50 dark:bg-brand-900/30 text-brand-700 dark:text-brand-300"
              : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700/50 hover:text-gray-900 dark:hover:text-white"
            }`
          }
        >
          <span className="text-base w-5 text-center shrink-0">🏠</span>
          {t("common.home")}
        </NavLink>

        <div className="px-3 py-1.5 space-y-2">
          <ThemeSwitcher />
          <LanguageSwitcher />
        </div>

        <button
          onClick={handleLogout}
          className="w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium text-gray-600 dark:text-gray-400 hover:bg-red-50 dark:hover:bg-red-900/20 hover:text-red-600 dark:hover:text-red-400 transition-colors"
        >
          <span className="text-base w-5 text-center shrink-0">↩</span>
          {t("common.signOut")}
        </button>
      </div>
    </div>
  );
}

export default function Sidebar() {
  const [open, setOpen] = useState(false);

  return (
    <>
      {/* Desktop sidebar — uses logical `start` so it flips to right in RTL automatically */}
      <aside className="hidden lg:flex flex-col fixed top-0 start-0 h-screen w-64
        bg-white dark:bg-gray-900 border-e border-gray-200 dark:border-gray-700/60 z-30">
        <SidebarContent />
      </aside>

      {/* Mobile hamburger — top-start corner */}
      <button
        className="lg:hidden fixed top-3 start-3 z-40 w-9 h-9 flex items-center justify-center
          bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700
          rounded-lg shadow text-gray-600 dark:text-gray-300"
        onClick={() => setOpen(true)}
        aria-label="Open menu"
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      </button>

      {/* Mobile drawer */}
      {open && (
        <>
          <div
            className="lg:hidden fixed inset-0 bg-black/50 backdrop-blur-sm z-40"
            onClick={() => setOpen(false)}
          />
          <aside className="lg:hidden fixed top-0 start-0 h-screen w-64
            bg-white dark:bg-gray-900 border-e border-gray-200 dark:border-gray-700/60
            z-50 shadow-2xl">
            <button
              className="absolute top-3 end-3 w-8 h-8 flex items-center justify-center
                rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-200
                hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-sm"
              onClick={() => setOpen(false)}
            >
              ✕
            </button>
            <SidebarContent onClose={() => setOpen(false)} />
          </aside>
        </>
      )}
    </>
  );
}
