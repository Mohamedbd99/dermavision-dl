import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import LanguageDetector from "i18next-browser-languagedetector";

import en from "./locales/en.json";
import fr from "./locales/fr.json";
import ar from "./locales/ar.json";

const RTL_LANGS = ["ar"];

function applyDir(lng: string) {
  const dir = RTL_LANGS.includes(lng) ? "rtl" : "ltr";
  document.documentElement.dir  = dir;
  document.documentElement.lang = lng;
  // swap font for Arabic
  document.documentElement.classList.toggle("font-arabic", lng === "ar");
}

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: { en: { translation: en }, fr: { translation: fr }, ar: { translation: ar } },
    fallbackLng: "en",
    supportedLngs: ["en", "fr", "ar"],
    detection: {
      order: ["localStorage", "navigator"],
      caches: ["localStorage"],
      lookupLocalStorage: "dermavision_lang",
    },
    interpolation: { escapeValue: false },
  });

// Apply on init
applyDir(i18n.language);

// Apply on every subsequent change
i18n.on("languageChanged", applyDir);

export default i18n;
