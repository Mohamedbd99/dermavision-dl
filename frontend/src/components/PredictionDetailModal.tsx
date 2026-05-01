import React from "react";
import { HistoryItem } from "../services/predict";

const CLASS_LABELS: Record<string, string> = {
  MEL:   "Melanoma",
  NV:    "Melanocytic Nevi",
  BCC:   "Basal Cell Carcinoma",
  AK:    "Actinic Keratosis",
  AKIEC: "Actinic Keratosis",
  BKL:   "Benign Keratosis",
  DF:    "Dermatofibroma",
  VASC:  "Vascular Lesion",
};

const RISK_CONFIG: Record<string, { label: string; bar: string; badge: string }> = {
  MEL:   { label: "High risk",          bar: "bg-red-500",    badge: "bg-red-100    text-red-700    dark:bg-red-900/40    dark:text-red-300"    },
  BCC:   { label: "Moderate–high risk", bar: "bg-orange-500", badge: "bg-orange-100 text-orange-700 dark:bg-orange-900/40 dark:text-orange-300" },
  AK:    { label: "Moderate risk",      bar: "bg-yellow-500", badge: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300" },
  AKIEC: { label: "Moderate risk",      bar: "bg-yellow-500", badge: "bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300" },
  NV:    { label: "Low risk",           bar: "bg-green-500",  badge: "bg-green-100  text-green-700  dark:bg-green-900/40  dark:text-green-300"  },
  BKL:   { label: "Low risk",           bar: "bg-green-500",  badge: "bg-green-100  text-green-700  dark:bg-green-900/40  dark:text-green-300"  },
  DF:    { label: "Low risk",           bar: "bg-green-500",  badge: "bg-green-100  text-green-700  dark:bg-green-900/40  dark:text-green-300"  },
  VASC:  { label: "Low risk",           bar: "bg-purple-500", badge: "bg-purple-100 text-purple-700 dark:bg-purple-900/40 dark:text-purple-300" },
};

interface Props {
  item: HistoryItem | null;
  onClose: () => void;
}

export default function PredictionDetailModal({ item, onClose }: Props) {
  if (!item) return null;

  const risk = RISK_CONFIG[item.predicted_class];

  const scores = Object.entries(item.all_scores ?? {})
    .map(([code, prob]) => ({
      code,
      label: CLASS_LABELS[code] ?? code,
      prob,
      bar: RISK_CONFIG[code]?.bar ?? "bg-brand-500",
    }))
    .sort((a, b) => b.prob - a.prob);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 dark:bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-xl max-h-[90vh] overflow-y-auto card !p-0 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-gray-100 dark:border-gray-700">
          <h2 className="text-base font-semibold text-gray-900 dark:text-gray-100">
            Prediction Detail
          </h2>
          <button
            onClick={onClose}
            className="w-8 h-8 flex items-center justify-center rounded-lg text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors text-sm"
          >
            ✕
          </button>
        </div>

        <div className="px-6 py-5 space-y-5">
          {/* Image + top info */}
          <div className="flex gap-4">
            <div className="flex-shrink-0">
              {item.image_url ? (
                <img
                  src={item.image_url}
                  alt={item.filename}
                  className="w-36 h-36 object-cover rounded-xl border border-gray-200 dark:border-gray-600"
                />
              ) : (
                <div className="w-36 h-36 flex items-center justify-center rounded-xl border border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 text-gray-400 text-xs text-center px-2">
                  No image
                </div>
              )}
            </div>

            <div className="flex-1 min-w-0 space-y-3">
              <div>
                <p className="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-1">Diagnosis</p>
                <div className="flex items-center gap-2 flex-wrap">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${risk?.badge ?? "bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300"}`}>
                    {item.predicted_class}
                  </span>
                  <span className="text-sm font-semibold text-gray-900 dark:text-gray-100">
                    {CLASS_LABELS[item.predicted_class] ?? item.predicted_class}
                  </span>
                </div>
              </div>

              <div>
                <p className="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-1">Confidence</p>
                <p className="text-2xl font-bold text-brand-600 dark:text-brand-400">
                  {(item.confidence * 100).toFixed(1)}%
                </p>
              </div>

              {risk && (
                <div>
                  <p className="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-1">Risk level</p>
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${risk.badge}`}>
                    {risk.label}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Date + File */}
          <div className="grid grid-cols-2 gap-4 py-3 border-t border-b border-gray-100 dark:border-gray-700 text-sm">
            <div>
              <p className="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-0.5">Date</p>
              <p className="text-gray-700 dark:text-gray-300">{new Date(item.created_at).toLocaleString()}</p>
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-0.5">File</p>
              <p className="text-gray-700 dark:text-gray-300 truncate">{item.filename}</p>
            </div>
          </div>

          {/* All class scores */}
          <div>
            <p className="text-xs font-medium text-gray-400 dark:text-gray-500 uppercase tracking-wide mb-3">All class scores</p>
            <div className="space-y-2.5">
              {scores.map(({ code, label, prob, bar }) => (
                <div key={code}>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm text-gray-700 dark:text-gray-300">
                      <span className="font-medium">{code}</span>
                      <span className="text-gray-400 dark:text-gray-500"> — {label}</span>
                    </span>
                    <span className="text-sm font-semibold text-gray-900 dark:text-gray-100 tabular-nums">
                      {(prob * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-100 dark:bg-gray-700 rounded-full h-1.5">
                    <div
                      className={`h-1.5 rounded-full transition-all ${bar}`}
                      style={{ width: `${(prob * 100).toFixed(1)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
