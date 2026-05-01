import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useTranslation } from "react-i18next";
import ThemeSwitcher from "../components/ThemeSwitcher";
import LanguageSwitcher from "../components/LanguageSwitcher";

const STEP_IMGS = [
  { n: 1, img: "/screenshots/step-1.png" },
  { n: 2, img: "/screenshots/step-2.png" },
  { n: 3, img: "/screenshots/step-3.png" },
  { n: 4, img: "/screenshots/step-4.png" },
  { n: 5, img: "/screenshots/step-5.png" },
  { n: 6, img: "/screenshots/step-6.png" },
];

const CLASSES = [
  { code: "MEL",  riskKey: "riskHigh",         color: "text-red-500",    bg: "bg-red-500/10"    },
  { code: "BCC",  riskKey: "riskModerateHigh",  color: "text-orange-500", bg: "bg-orange-500/10" },
  { code: "AK",   riskKey: "riskModerate",      color: "text-yellow-500", bg: "bg-yellow-500/10" },
  { code: "NV",   riskKey: "riskBenign",        color: "text-green-500",  bg: "bg-green-500/10"  },
  { code: "BKL",  riskKey: "riskBenign",        color: "text-green-500",  bg: "bg-green-500/10"  },
  { code: "DF",   riskKey: "riskBenign",        color: "text-green-500",  bg: "bg-green-500/10"  },
  { code: "VASC", riskKey: "riskBenign",        color: "text-purple-500", bg: "bg-purple-500/10" },
];

function StepImage({ src, alt, n }: { src: string; alt: string; n: number }) {
  const [errored, setErrored] = useState(false);
  return (
    <div className="rounded-2xl overflow-hidden border border-gray-200 dark:border-gray-700 shadow-2xl bg-gray-900">
      <div className="flex items-center gap-1.5 px-4 py-2.5 bg-gray-800 border-b border-gray-700">
        <span className="w-3 h-3 rounded-full bg-red-500/80" />
        <span className="w-3 h-3 rounded-full bg-yellow-500/80" />
        <span className="w-3 h-3 rounded-full bg-green-500/80" />
        <span className="ms-3 text-xs text-gray-400 font-mono">localhost:3000</span>
      </div>
      {!errored ? (
        <img src={src} alt={alt} className="w-full object-cover" onError={() => setErrored(true)} />
      ) : (
        <div className="w-full aspect-video flex flex-col items-center justify-center gap-2 text-gray-500">
          <span className="text-4xl">📷</span>
          <p className="text-sm font-medium">Step {n}</p>
          <p className="text-xs opacity-60">public/screenshots/step-{n}.png</p>
        </div>
      )}
    </div>
  );
}

export default function LandingPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslation();

  const STATS = [
    { value: "0.9776", label: "AUC-ROC" },
    { value: "85.4%",  label: t("dashboard.accuracy") },
    { value: "0.796",  label: "F1-macro" },
    { value: "10,015", label: t("landing.statsImages") },
  ];

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100">

      {/* ── Sticky nav ─────────────────────────────────────────── */}
      <header className="sticky top-0 z-30 bg-white/80 dark:bg-gray-950/80 backdrop-blur-md border-b border-gray-100 dark:border-gray-800">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="text-xl">🔬</span>
            <span className="font-bold text-gray-900 dark:text-white">{t("common.appName")}</span>
          </div>
          <div className="flex items-center gap-2">
            <LanguageSwitcher />
            <ThemeSwitcher />
            {user ? (
              <button onClick={() => navigate("/predict")} className="btn-primary text-sm ms-1">
                {t("common.goToApp")}
              </button>
            ) : (
              <>
                <Link to="/login"    className="btn-secondary text-sm">{t("common.signIn")}</Link>
                <Link to="/register" className="btn-primary   text-sm">{t("common.getStarted")}</Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* ── Hero ───────────────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-4 pt-24 pb-16 text-center">
        <div className="inline-flex items-center gap-2 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 text-xs font-semibold px-4 py-1.5 rounded-full mb-6 tracking-wide">
          🏆 &nbsp; {t("landing.badge")}
        </div>
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-tight mb-6">
          {t("landing.heroHeadline")}
          <br className="hidden sm:block" />
          <span className="text-brand-600 dark:text-brand-400"> {t("landing.heroHighlight")}</span>
        </h1>
        <p className="text-lg sm:text-xl text-gray-500 dark:text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          {t("landing.heroSub")}
        </p>
        <div className="flex flex-wrap items-center justify-center gap-4">
          {user ? (
            <button onClick={() => navigate("/predict")} className="btn-primary text-base px-8 py-3">
              🔍 {t("common.analyse")}
            </button>
          ) : (
            <>
              <Link to="/register" className="btn-primary  text-base px-8 py-3">{t("landing.getStartedFree")}</Link>
              <Link to="/login"    className="btn-secondary text-base px-8 py-3">{t("common.signIn")}</Link>
            </>
          )}
        </div>
      </section>

      {/* ── Stats bar ──────────────────────────────────────────── */}
      <section className="bg-gray-50 dark:bg-gray-900 border-y border-gray-100 dark:border-gray-800 py-10">
        <div className="max-w-6xl mx-auto px-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 text-center">
            {STATS.map(({ value, label }) => (
              <div key={label}>
                <p className="text-3xl font-bold text-brand-600 dark:text-brand-400">{value}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it works ───────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold mb-3">{t("landing.howItWorks")}</h2>
          <p className="text-gray-500 dark:text-gray-400 text-lg">{t("landing.howItWorksSub")}</p>
        </div>

        <div className="space-y-24">
          {STEP_IMGS.map(({ n, img }, i) => (
            <div
              key={n}
              className={`flex flex-col ${i % 2 === 0 ? "lg:flex-row" : "lg:flex-row-reverse"} items-center gap-10 lg:gap-16`}
            >
              <div className="w-full lg:w-1/2">
                <StepImage src={img} alt={`Step ${n}`} n={n} />
              </div>
              <div className="w-full lg:w-1/2 space-y-4">
                <div className="inline-flex items-center justify-center w-11 h-11 rounded-full bg-brand-600 text-white font-bold text-lg shadow-lg shadow-brand-600/30">
                  {n}
                </div>
                <h3 className="text-2xl sm:text-3xl font-bold">{t(`landing.step${n}Title`)}</h3>
                <p className="text-gray-500 dark:text-gray-400 text-lg leading-relaxed">{t(`landing.step${n}Desc`)}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Classes ────────────────────────────────────────────── */}
      <section className="bg-gray-50 dark:bg-gray-900 border-t border-gray-100 dark:border-gray-800 py-20">
        <div className="max-w-6xl mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-3">{t("landing.classesTitle")}</h2>
            <p className="text-gray-500 dark:text-gray-400">{t("landing.classesSub")}</p>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {CLASSES.map(({ code, riskKey, color, bg }) => (
              <div key={code} className="card flex flex-col gap-2">
                <span className={`inline-flex w-fit px-2.5 py-0.5 rounded text-xs font-bold ${bg} ${color}`}>
                  {code}
                </span>
                <p className="font-semibold text-sm text-gray-900 dark:text-gray-100">
                  {t(`classes.${code}`, { defaultValue: code })}
                </p>
                <p className={`text-xs font-medium ${color}`}>{t(`landing.${riskKey}`)}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ────────────────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-4 py-24 text-center">
        <h2 className="text-3xl sm:text-4xl font-bold mb-4">{t("landing.ctaTitle")}</h2>
        <p className="text-gray-500 dark:text-gray-400 mb-8 max-w-xl mx-auto text-lg">{t("landing.ctaSub")}</p>
        {user ? (
          <button onClick={() => navigate("/predict")} className="btn-primary text-base px-8 py-3">
            🔍 {t("common.analyse")}
          </button>
        ) : (
          <Link to="/register" className="btn-primary text-base px-8 py-3">
            {t("landing.createFreeAccount")}
          </Link>
        )}
      </section>

      {/* ── Footer ─────────────────────────────────────────────── */}
      <footer className="border-t border-gray-100 dark:border-gray-800 py-6">
        <p className="text-center text-xs text-gray-400 dark:text-gray-500">
          {t("common.appName")} · EfficientNet-B3 · HAM10000 · AUC 0.9776 ·{" "}
          <strong>{t("common.disclaimer")}</strong>
          {" "}·{" "}
          <a
            href="https://github.com/Mohamedbd99/dermavision-dl"
            target="_blank"
            rel="noreferrer"
            className="hover:underline"
          >
            {t("common.github")}
          </a>
        </p>
      </footer>
    </div>
  );
}
