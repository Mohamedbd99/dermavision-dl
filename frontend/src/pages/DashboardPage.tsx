import React, { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { getHistory, getMetrics, HistoryItem } from "../services/predict";
import { useNavigate } from "react-router-dom";

const CLASS_FULL: Record<string, string> = {
  MEL:   "Melanoma",
  NV:    "Melanocytic Nevi",
  BCC:   "Basal Cell Carcinoma",
  AKIEC: "Actinic Keratosis",
  BKL:   "Benign Keratosis",
  DF:    "Dermatofibroma",
  VASC:  "Vascular Lesion",
};

const RISK: Record<string, { label: string; color: string }> = {
  MEL:   { label: "High risk — consult dermatologist", color: "text-red-600"    },
  BCC:   { label: "Moderate–High risk",                 color: "text-orange-600" },
  AKIEC: { label: "Moderate risk",                      color: "text-yellow-600" },
  NV:    { label: "Low risk (benign)",                  color: "text-green-600"  },
  BKL:   { label: "Low risk (benign)",                  color: "text-green-600"  },
  DF:    { label: "Low risk (benign)",                  color: "text-green-600"  },
  VASC:  { label: "Low risk (benign)",                  color: "text-green-600"  },
};

interface Metrics {
  total_predictions: number;
  accuracy?: number;
  f1_macro?: number;
  auc_roc?: number;
}

export default function DashboardPage() {
  const { user, logout }  = useAuth();
  const navigate           = useNavigate();
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([getHistory(), getMetrics()])
      .then(([hist, met]) => {
        setHistory(hist);
        setMetrics(met as unknown as Metrics);
      })
      .finally(() => setLoading(false));
  }, []);

  const handleLogout = () => { logout(); navigate("/login"); };

  return (
    <div className="max-w-5xl mx-auto px-4 py-10 space-y-8">
      {/* Top bar */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-sm text-gray-500">
            Welcome, <strong>{user?.username}</strong>
          </p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => navigate("/predict")} className="btn-primary text-sm">
            🔍 New prediction
          </button>
          <button onClick={handleLogout} className="btn-secondary text-sm">
            Sign out
          </button>
        </div>
      </div>

      {/* Model stats */}
      {metrics && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          {[
            { label: "Total predictions", value: metrics.total_predictions ?? "—" },
            { label: "Accuracy",          value: metrics.accuracy  ? `${(metrics.accuracy  * 100).toFixed(1)}%` : "—" },
            { label: "F1-macro",          value: metrics.f1_macro  ? metrics.f1_macro.toFixed(3)                : "—" },
            { label: "AUC-ROC",           value: metrics.auc_roc   ? metrics.auc_roc.toFixed(4)                 : "—" },
          ].map(({ label, value }) => (
            <div key={label} className="card text-center">
              <p className="text-2xl font-bold text-brand-600">{value}</p>
              <p className="text-xs text-gray-500 mt-1">{label}</p>
            </div>
          ))}
        </div>
      )}

      {/* Prediction history */}
      <div className="card">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">My Prediction History</h2>
        {loading ? (
          <p className="text-gray-400 text-sm">Loading…</p>
        ) : history.length === 0 ? (
          <p className="text-gray-400 text-sm">No predictions yet. Go analyse an image!</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b text-left text-gray-500">
                  <th className="pb-2 pr-4">File</th>
                  <th className="pb-2 pr-4">Prediction</th>
                  <th className="pb-2 pr-4">Confidence</th>
                  <th className="pb-2 pr-4">Risk</th>
                  <th className="pb-2">Date</th>
                </tr>
              </thead>
              <tbody>
                {history.map((item) => (
                  <tr key={item.id} className="border-b last:border-0 hover:bg-gray-50">
                    <td className="py-3 pr-4 truncate max-w-[150px] text-gray-700">{item.filename}</td>
                    <td className="py-3 pr-4 font-medium text-gray-900">
                      {CLASS_FULL[item.prediction] ?? item.prediction}
                    </td>
                    <td className="py-3 pr-4 text-gray-600">
                      {(item.confidence * 100).toFixed(1)}%
                    </td>
                    <td className={`py-3 pr-4 text-xs font-medium ${RISK[item.prediction]?.color ?? "text-gray-500"}`}>
                      {RISK[item.prediction]?.label ?? "—"}
                    </td>
                    <td className="py-3 text-gray-400 whitespace-nowrap">
                      {new Date(item.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <p className="text-xs text-gray-400 text-center">
        DermaVision · EfficientNet-B3 · HAM10000 · AUC 0.9776 · For research use only
      </p>
    </div>
  );
}
