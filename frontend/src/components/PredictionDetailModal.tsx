import React from 'react'
import { HistoryItem } from '../services/predict'

const CLASS_LABELS: Record<string, string> = {
  MEL: 'Melanoma',
  NV:  'Melanocytic Nevi',
  BCC: 'Basal Cell Carcinoma',
  AK:  'Actinic Keratosis',
  BKL: 'Benign Keratosis',
  DF:  'Dermatofibroma',
  VASC:'Vascular Lesion',
}

const RISK_COLOR: Record<string, string> = {
  MEL:  '#ef4444',
  BCC:  '#f97316',
  AK:   '#eab308',
  NV:   '#22c55e',
  BKL:  '#22c55e',
  DF:   '#22c55e',
  VASC: '#a855f7',
}

interface Props {
  item: HistoryItem | null
  onClose: () => void
}

export default function PredictionDetailModal({ item, onClose }: Props) {
  if (!item) return null

  const scores = Object.entries(item.all_scores ?? {})
    .map(([code, prob]) => ({ code, label: CLASS_LABELS[code] ?? code, prob }))
    .sort((a, b) => b.prob - a.prob)

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative bg-gray-900 border border-gray-700 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto p-6"
        onClick={e => e.stopPropagation()}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-white text-xl font-bold leading-none"
        >
          ×
        </button>

        <h2 className="text-xl font-bold text-white mb-4">Prediction Detail</h2>

        <div className="flex flex-col md:flex-row gap-6">
          {/* Image */}
          <div className="flex-shrink-0">
            {item.image_url ? (
              <img
                src={item.image_url}
                alt={item.filename}
                className="w-52 h-52 object-cover rounded-xl border border-gray-700"
              />
            ) : (
              <div className="w-52 h-52 flex items-center justify-center bg-gray-800 rounded-xl border border-gray-700 text-gray-500 text-sm">
                No image
              </div>
            )}
          </div>

          {/* Info */}
          <div className="flex-1 space-y-4">
            {/* Top prediction badge */}
            <div>
              <span className="text-xs uppercase tracking-widest text-gray-400">Diagnosis</span>
              <div className="mt-1 flex items-center gap-2">
                <span
                  className="px-3 py-1 rounded-full text-sm font-semibold text-white"
                  style={{ backgroundColor: RISK_COLOR[item.predicted_class] ?? '#6b7280' }}
                >
                  {item.predicted_class}
                </span>
                <span className="text-white font-medium">
                  {CLASS_LABELS[item.predicted_class] ?? item.predicted_class}
                </span>
              </div>
            </div>

            {/* Confidence */}
            <div>
              <span className="text-xs uppercase tracking-widest text-gray-400">Confidence</span>
              <p className="mt-1 text-2xl font-bold text-white">
                {(item.confidence * 100).toFixed(1)}%
              </p>
            </div>

            {/* Date */}
            <div>
              <span className="text-xs uppercase tracking-widest text-gray-400">Date</span>
              <p className="mt-1 text-gray-300 text-sm">
                {new Date(item.created_at).toLocaleString()}
              </p>
            </div>

            {/* Filename */}
            <div>
              <span className="text-xs uppercase tracking-widest text-gray-400">File</span>
              <p className="mt-1 text-gray-300 text-sm truncate max-w-xs">{item.filename}</p>
            </div>
          </div>
        </div>

        {/* All class scores */}
        <div className="mt-6">
          <h3 className="text-sm uppercase tracking-widest text-gray-400 mb-3">All Class Scores</h3>
          <div className="space-y-2">
            {scores.map(({ code, label, prob }) => (
              <div key={code}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-300">
                    <span
                      className="inline-block w-2 h-2 rounded-full mr-2"
                      style={{ backgroundColor: RISK_COLOR[code] ?? '#6b7280' }}
                    />
                    {code} – {label}
                  </span>
                  <span className="text-white font-medium">{(prob * 100).toFixed(1)}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className="h-2 rounded-full transition-all"
                    style={{
                      width: `${(prob * 100).toFixed(1)}%`,
                      backgroundColor: RISK_COLOR[code] ?? '#6b7280',
                    }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
