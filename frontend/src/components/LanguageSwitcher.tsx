import React from "react";
import { useTranslation } from "react-i18next";

const LANGS = [
  { code: "en", label: "EN" },
  { code: "fr", label: "FR" },
  { code: "ar", label: "AR" },
];

export default function LanguageSwitcher() {
  const { i18n } = useTranslation();
  const current = i18n.language?.slice(0, 2);

  return (
    <div className="flex items-center gap-0.5 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
      {LANGS.map(({ code, label }) => (
        <button
          key={code}
          onClick={() => i18n.changeLanguage(code)}
          title={label}
          className={`px-2.5 py-1 rounded-md text-xs font-semibold transition-all duration-150 ${
            current === code
              ? "bg-white dark:bg-gray-900 shadow-sm text-gray-900 dark:text-white"
              : "text-gray-400 dark:text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  );
}
