import React from "react";
import { useTheme, Theme } from "../context/ThemeContext";

const OPTIONS: { value: Theme; icon: string; label: string }[] = [
  { value: "light",  icon: "☀️", label: "Light"  },
  { value: "dark",   icon: "🌙", label: "Dark"   },
  { value: "system", icon: "💻", label: "System" },
];

export default function ThemeSwitcher() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="flex items-center gap-0.5 bg-gray-100 dark:bg-gray-700 rounded-lg p-1">
      {OPTIONS.map((o) => (
        <button
          key={o.value}
          onClick={() => setTheme(o.value)}
          title={o.label}
          className={`px-2.5 py-1 rounded-md text-sm transition-all duration-150 ${
            theme === o.value
              ? "bg-white dark:bg-gray-900 shadow-sm text-gray-900 dark:text-white font-medium"
              : "text-gray-400 dark:text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
          }`}
        >
          {o.icon}
        </button>
      ))}
    </div>
  );
}
