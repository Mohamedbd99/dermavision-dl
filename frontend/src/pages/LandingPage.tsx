import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import ThemeSwitcher from "../components/ThemeSwitcher";

const STEPS = [
  {
    n: 1,
    title: "Create your account",
    desc: "Sign up in seconds — no credit card required. Your data stays private and encrypted.",
    img: "/screenshots/step-1.png",
    alt: "Login page",
  },
  {
    n: 2,
    title: "Register & get started",
    desc: "Fill in your username and password. You'll be taken straight to the analyser.",
    img: "/screenshots/step-2.png",
    alt: "Register page",
  },
  {
    n: 3,
    title: "Upload your dermoscopy image",
    desc: "Drag & drop or browse for a JPG/PNG image. The model accepts any dermoscopy or clinical photo.",
    img: "/screenshots/step-3.png",
    alt: "Image upload interface",
  },
  {
    n: 4,
    title: "Get instant AI analysis",
    desc: "EfficientNet-B3 returns a ranked probability breakdown across all 7 lesion classes in under a second.",
    img: "/screenshots/step-4.png",
    alt: "AI prediction results with probability bars",
  },
  {
    n: 5,
    title: "Track your history",
    desc: "Every analysis is saved to your personal dashboard. Review past results and model stats anytime.",
    img: "/screenshots/step-5.png",
    alt: "Dashboard with prediction history",
  },
  {
    n: 6,
    title: "Explore detailed insights",
    desc: "Click any row to see the full breakdown — original image, confidence, risk level, and scores for all classes.",
    img: "/screenshots/step-6.png",
    alt: "Detailed prediction breakdown modal",
  },
];

const STATS = [
  { value: "0.9776", label: "AUC-ROC"         },
  { value: "85.4%",  label: "Accuracy"        },
  { value: "0.796",  label: "F1-macro"        },
  { value: "10,015", label: "Training images" },
];

const CLASSES = [
  { code: "MEL",  name: "Melanoma",             risk: "High risk",     color: "text-red-500",    bg: "bg-red-500/10"    },
  { code: "BCC",  name: "Basal Cell Carcinoma", risk: "Moderate-high", color: "text-orange-500", bg: "bg-orange-500/10" },
  { code: "AK",   name: "Actinic Keratosis",    risk: "Moderate",      color: "text-yellow-500", bg: "bg-yellow-500/10" },
  { code: "NV",   name: "Melanocytic Nevi",     risk: "Benign",        color: "text-green-500",  bg: "bg-green-500/10"  },
  { code: "BKL",  name: "Benign Keratosis",     risk: "Benign",        color: "text-green-500",  bg: "bg-green-500/10"  },
  { code: "DF",   name: "Dermatofibroma",       risk: "Benign",        color: "text-green-500",  bg: "bg-green-500/10"  },
  { code: "VASC", name: "Vascular Lesion",      risk: "Benign",        color: "text-purple-500", bg: "bg-purple-500/10" },
];

function StepImage({ src, alt, n }: { src: string; alt: string; n: number }) {
  const [errored, setErrored] = useState(false);
  return (
    <div className="rounded-2xl overflow-hidden border border-gray-200 dark:border-gray-700 shadow-2xl bg-gray-900">
      {/* Browser chrome */}
      <div className="flex items-center gap-1.5 px-4 py-2.5 bg-gray-800 border-b border-gray-700">
        <span className="w-3 h-3 rounded-full bg-red-500/80" />
        <span className="w-3 h-3 rounded-full bg-yellow-500/80" />
        <span className="w-3 h-3 rounded-full bg-green-500/80" />
        <span className="ml-3 text-xs text-gray-400 font-mono">localhost:3000</span>
      </div>
      {!errored ? (
        <img
          src={src}
          alt={alt}
          className="w-full object-cover"
          onError={() => setErrored(true)}
        />
      ) : (
        <div className="w-full aspect-video flex flex-col items-center justify-center gap-2 text-gray-500">
          <span className="text-4xl">📷</span>
          <p className="text-sm font-medium">Step {n} screenshot</p>
          <p className="text-xs opacity-60">Add file: public/screenshots/step-{n}.png</p>
        </div>
      )}
    </div>
  );
}

export default function LandingPage() {
  const { user } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-white dark:bg-gray-950 text-gray-900 dark:text-gray-100">

      {/* ── Sticky nav ─────────────────────────────────────────── */}
      <header className="sticky top-0 z-30 bg-white/80 dark:bg-gray-950/80 backdrop-blur-md border-b border-gray-100 dark:border-gray-800">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="text-xl">🔬</span>
            <span className="font-bold text-gray-900 dark:text-white">DermaVision</span>
          </div>
          <div className="flex items-center gap-3">
            <ThemeSwitcher />
            {user ? (
              <button onClick={() => navigate("/predict")} className="btn-primary text-sm">
                Go to app →
              </button>
            ) : (
              <>
                <Link to="/login"    className="btn-secondary text-sm">Sign in</Link>
                <Link to="/register" className="btn-primary  text-sm">Get started</Link>
              </>
            )}
          </div>
        </div>
      </header>

      {/* ── Hero ───────────────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-4 pt-24 pb-16 text-center">
        <div className="inline-flex items-center gap-2 bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 text-xs font-semibold px-4 py-1.5 rounded-full mb-6 tracking-wide">
          🏆 &nbsp; EfficientNet-B3 · HAM10000 · AUC-ROC 0.9776
        </div>
        <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight leading-tight mb-6">
          AI-powered skin lesion
          <br className="hidden sm:block" />
          <span className="text-brand-600 dark:text-brand-400"> classification</span>
        </h1>
        <p className="text-lg sm:text-xl text-gray-500 dark:text-gray-400 max-w-2xl mx-auto mb-10 leading-relaxed">
          Upload a dermoscopy image and get instant probability scores across
          7 skin lesion categories — powered by a deep learning model trained
          on 10,015 clinical images.
        </p>
        <div className="flex flex-wrap items-center justify-center gap-4">
          {user ? (
            <button onClick={() => navigate("/predict")} className="btn-primary text-base px-8 py-3">
              🔍 Analyse an image
            </button>
          ) : (
            <>
              <Link to="/register" className="btn-primary  text-base px-8 py-3">Get started free →</Link>
              <Link to="/login"    className="btn-secondary text-base px-8 py-3">Sign in</Link>
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
          <h2 className="text-3xl sm:text-4xl font-bold mb-3">How it works</h2>
          <p className="text-gray-500 dark:text-gray-400 text-lg">Your first analysis in under a minute</p>
        </div>

        <div className="space-y-24">
          {STEPS.map((step, i) => (
            <div
              key={step.n}
              className={`flex flex-col ${i % 2 === 0 ? "lg:flex-row" : "lg:flex-row-reverse"} items-center gap-10 lg:gap-16`}
            >
              {/* Screenshot */}
              <div className="w-full lg:w-1/2">
                <StepImage src={step.img} alt={step.alt} n={step.n} />
              </div>

              {/* Text */}
              <div className="w-full lg:w-1/2 space-y-4">
                <div className="inline-flex items-center justify-center w-11 h-11 rounded-full bg-brand-600 text-white font-bold text-lg shadow-lg shadow-brand-600/30">
                  {step.n}
                </div>
                <h3 className="text-2xl sm:text-3xl font-bold">{step.title}</h3>
                <p className="text-gray-500 dark:text-gray-400 text-lg leading-relaxed">{step.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ── Classes ────────────────────────────────────────────── */}
      <section className="bg-gray-50 dark:bg-gray-900 border-t border-gray-100 dark:border-gray-800 py-20">
        <div className="max-w-6xl mx-auto px-4">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold mb-3">7 lesion classes detected</h2>
            <p className="text-gray-500 dark:text-gray-400">
              Trained on the HAM10000 / ISIC 2018 clinical dataset
            </p>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
            {CLASSES.map(({ code, name, risk, color, bg }) => (
              <div key={code} className="card flex flex-col gap-2">
                <span className={`inline-flex w-fit px-2.5 py-0.5 rounded text-xs font-bold ${bg} ${color}`}>
                  {code}
                </span>
                <p className="font-semibold text-sm text-gray-900 dark:text-gray-100">{name}</p>
                <p className={`text-xs font-medium ${color}`}>{risk}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ────────────────────────────────────────────────── */}
      <section className="max-w-6xl mx-auto px-4 py-24 text-center">
        <h2 className="text-3xl sm:text-4xl font-bold mb-4">
          Ready to analyse your first image?
        </h2>
        <p className="text-gray-500 dark:text-gray-400 mb-8 max-w-xl mx-auto text-lg">
          Free to use. No setup required. Create an account and get your first
          result in seconds.
        </p>
        {user ? (
          <button onClick={() => navigate("/predict")} className="btn-primary text-base px-8 py-3">
            🔍 Analyse an image
          </button>
        ) : (
          <Link to="/register" className="btn-primary text-base px-8 py-3">
            Create free account →
          </Link>
        )}
      </section>

      {/* ── Footer ─────────────────────────────────────────────── */}
      <footer className="border-t border-gray-100 dark:border-gray-800 py-6">
        <p className="text-center text-xs text-gray-400 dark:text-gray-500">
          DermaVision · EfficientNet-B3 · HAM10000 · AUC 0.9776 ·{" "}
          <strong>For research and educational use only. Not a medical device.</strong>
          {" "}·{" "}
          <a
            href="https://github.com/Mohamedbd99/dermavision-dl"
            target="_blank"
            rel="noreferrer"
            className="hover:underline"
          >
            GitHub
          </a>
        </p>
      </footer>
    </div>
  );
}
