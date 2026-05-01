import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { getHistory, getMetrics, HistoryItem } from "../services/predict";
import PredictionDetailModal from "../components/PredictionDetailModal";
import { useTranslation } from "react-i18next";

const RISK_COLOR: Record<string, string> = {
  MEL:   "text-red-600",
  BCC:   "text-orange-600",
  AK:    "text-yellow-600",
  AKIEC: "text-yellow-600",
  NV:    "text-green-600",
  BKL:   "text-green-600",
  DF:    "text-green-600",
  VASC:  "text-green-600",
};

interface Metrics {
  metrics?: { accuracy?: number; f1_macro?: number; auc_roc_macro_ovr?: number; };
  total_predictions?: number;
}

export default function DashboardPage() {
  const { user }  = useAuth();
  const { t } = useTranslation();
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedItem, setSelectedItem] = useState<HistoryItem | null>(null);

  useEffect(() => {
    Promise.all([getHistory(), getMetrics()])
      .then(([hist, met]) => {
        setHistory(hist);
        setMetrics(met as unknown as Metrics);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-5xl mx-auto px-4 py-10 space-y-8">
      {/* Page title */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{t("dashboard.title")}</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400">
          {t("dashboard.welcome", { username: user?.username })}
        </p>
      </div>

      {/* Model stats */}
      {metrics && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: t("dashboard.totalPredictions"), value: metrics.total_predictions ?? history.length },
            { label: t("dashboard.accuracy"),          value: metrics.metrics?.accuracy            ? `${(metrics.metrics.accuracy * 100).toFixed(1)}%` : "—" },
            { label: t("dashboard.f1Macro"),            value: metrics.metrics?.f1_macro            ? metrics.metrics.f1_macro.toFixed(3)              : "—" },
            { label: t("dashboard.aucRoc"),             value: metrics.metrics?.auc_roc_macro_ovr   ? metrics.metrics.auc_roc_macro_ovr.toFixed(4)     : "—" },
          ].map(({ label, value }) => (
            <div key={label} className="card text-center">
              <p className="text-2xl font-bold text-brand-600 dark:text-brand-400">{value}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Prediction history */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">{t("dashboard.historyTitle")}</h2>
        {loading ? (
          <p className="text-gray-400 text-sm">{t("dashboard.loading")}</p>
        ) : history.length === 0 ? (
          <p className="text-gray-400 text-sm">{t("dashboard.empty")}</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-gray-100 dark:border-gray-700 text-left rtl:text-right text-gray-500 dark:text-gray-400">
                  <th className="pb-2 pe-4">{t("dashboard.colFile")}</th>
                  <th className="pb-2 pe-4">{t("dashboard.colPrediction")}</th>
                  <th className="pb-2 pe-4">{t("dashboard.colConfidence")}</th>
                  <th className="pb-2 pe-4">{t("dashboard.colRisk")}</th>
                  <th className="pb-2">{t("dashboard.colDate")}</th>
                </tr>
              </thead>
              <tbody>
                {history.map((item) => (
                  <tr key={item.id} className="border-b border-gray-100 dark:border-gray-700 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-700/50 cursor-pointer" onClick={() => setSelectedItem(item)}>
                    <td className="py-3 pe-4 truncate max-w-[150px] text-gray-700 dark:text-gray-300">{item.filename}</td>
                    <td className="py-3 pe-4 font-medium text-gray-900 dark:text-gray-100">
                      {t(`classes.${item.predicted_class}`, { defaultValue: item.predicted_class })}
                    </td>
                    <td className="py-3 pe-4 text-gray-600 dark:text-gray-400">
                      {(item.confidence * 100).toFixed(1)}%
                    </td>
                    <td className={`py-3 pe-4 text-xs font-medium ${RISK_COLOR[item.predicted_class] ?? "text-gray-500"}`}>
                      {t(`risk.${item.predicted_class}`, { defaultValue: "—" })}
                    </td>
                    <td className="py-3 text-gray-400 dark:text-gray-500 whitespace-nowrap">
                      {new Date(item.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <PredictionDetailModal item={selectedItem} onClose={() => setSelectedItem(null)} />

      <p className="text-xs text-gray-400 text-center">
        {t("dashboard.footer")}
      </p>
    </div>
  );
}
