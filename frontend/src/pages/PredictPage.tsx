import React, { useCallback, useState } from "react";
import { predict, PredictionResult } from "../services/predict";

const CLASS_COLORS: Record<string, string> = {
  MEL:   "bg-red-500",
  NV:    "bg-blue-500",
  BCC:   "bg-orange-500",
  AKIEC: "bg-yellow-500",
  BKL:   "bg-green-500",
  DF:    "bg-purple-500",
  VASC:  "bg-pink-500",
};

export default function PredictPage() {
  const [file, setFile]         = useState<File | null>(null);
  const [preview, setPreview]   = useState<string | null>(null);
  const [result, setResult]     = useState<PredictionResult | null>(null);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState("");
  const [dragging, setDragging] = useState(false);

  const handleFile = (f: File) => {
    setFile(f);
    setPreview(URL.createObjectURL(f));
    setResult(null);
    setError("");
  };

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const f = e.dataTransfer.files[0];
    if (f) handleFile(f);
  }, []);

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) handleFile(f);
  };

  const handleSubmit = async () => {
    if (!file) return;
    setLoading(true);
    setError("");
    try {
      const res = await predict(file);
      setResult(res);
    } catch {
      setError("Prediction failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  // Sort scores descending
  const sortedScores = result
    ? [...result.scores].sort((a, b) => b.probability - a.probability)
    : [];

  return (
    <div className="max-w-3xl mx-auto px-4 py-10 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Skin Lesion Classifier</h1>
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Upload a dermoscopy image to get AI-powered analysis</p>
      </div>

      {/* Drop zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={`relative border-2 border-dashed rounded-xl flex flex-col items-center justify-center p-10 transition-colors cursor-pointer
          ${dragging
            ? "border-brand-500 bg-brand-50 dark:bg-brand-900/20"
            : "border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 hover:border-brand-400 hover:bg-gray-50 dark:hover:bg-gray-700/50"}`}
      >
        {preview ? (
          <img
            src={preview}
            alt="preview"
            className="max-h-64 rounded-lg object-contain shadow"
          />
        ) : (
          <>
            <span className="text-5xl mb-3">🖼️</span>
            <p className="text-gray-600 dark:text-gray-300 font-medium">Drag & drop an image here</p>
            <p className="text-gray-400 dark:text-gray-500 text-sm mt-1">or click to browse</p>
          </>
        )}
        <input
          type="file"
          accept="image/*"
          className="absolute inset-0 opacity-0 cursor-pointer"
          onChange={onFileChange}
        />
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={handleSubmit}
          disabled={!file || loading}
          className="btn-primary flex-1"
        >
          {loading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
              Analysing…
            </span>
          ) : "🔍 Analyse Image"}
        </button>
        {file && (
          <button
            onClick={() => { setFile(null); setPreview(null); setResult(null); }}
            className="btn-secondary"
          >
            Clear
          </button>
        )}
      </div>

      {error && (
        <p className="text-sm text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 rounded-lg px-3 py-2">
          {error}
        </p>
      )}

      {/* Results */}
      {result && (
        <div className="card space-y-5 animate-fade-in">
          <div className="flex items-center gap-3">
            <div className={`w-3 h-3 rounded-full ${CLASS_COLORS[result.prediction] ?? "bg-gray-400"}`} />
            <div>
              <p className="text-xs text-gray-500 dark:text-gray-400 uppercase tracking-wider">Top prediction</p>
              <p className="text-lg font-bold text-gray-900 dark:text-gray-100">
                {sortedScores[0]?.full_name ?? result.prediction}
                <span className="ml-2 text-brand-600">
                  {(result.confidence * 100).toFixed(1)}%
                </span>
              </p>
            </div>
          </div>

          {/* Probability bars — top 3 */}
          <div className="space-y-3">
            <p className="text-sm font-semibold text-gray-700 dark:text-gray-200">Top-3 Predictions</p>
            {sortedScores.slice(0, 3).map((s) => (
              <div key={s.label}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="font-medium text-gray-700 dark:text-gray-200">{s.full_name}</span>
                    <span className="text-gray-500 dark:text-gray-400">{(s.probability * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-100 dark:bg-gray-700 rounded-full h-2.5">
                  <div
                    className={`h-2.5 rounded-full ${CLASS_COLORS[s.label] ?? "bg-brand-500"}`}
                    style={{ width: `${s.probability * 100}%` }}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* All scores */}
          <details className="text-sm">
            <summary className="cursor-pointer text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200">
              Show all 7 class scores
            </summary>
            <div className="mt-3 space-y-2">
              {sortedScores.map((s) => (
                <div key={s.label} className="flex justify-between">
                    <span className="text-gray-600 dark:text-gray-300">{s.label} — {s.full_name}</span>
                    <span className="font-mono text-gray-700 dark:text-gray-200">{(s.probability * 100).toFixed(2)}%</span>
                </div>
              ))}
            </div>
          </details>

          <p className="text-xs text-gray-400 dark:text-gray-500 border-t border-gray-100 dark:border-gray-700 pt-3">
            ⚠️ This tool is for research purposes only. Always consult a dermatologist for diagnosis.
          </p>
        </div>
      )}
    </div>
  );
}
