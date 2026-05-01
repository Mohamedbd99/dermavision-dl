/** @type {import('tailwindcss').Config} */
export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50:  "#eef2ff",
          100: "#e0e7ff",
          500: "#6366f1",
          600: "#4f46e5",
          700: "#4338ca",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
      keyframes: {
        "toast-in": {
          "0%":   { opacity: "0", transform: "translateX(24px) scale(0.96)" },
          "100%": { opacity: "1", transform: "translateX(0)   scale(1)"    },
        },
      },
      animation: {
        "toast-in": "toast-in 0.2s ease-out both",
      },
    },
  },
  plugins: [],
};
