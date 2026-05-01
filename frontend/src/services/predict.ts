import api from "./api";

export interface PredictionScore {
  code: string;
  full_name: string;
  confidence: number;
  // normalised aliases used by the UI
  label: string;
  probability: number;
}

export interface PredictionResult {
  predicted_class: string;
  predicted_class_full: string;
  confidence: number;
  all_scores: PredictionScore[];
  filename: string;
  logged_at: string;
  // aliases so existing UI code keeps working
  prediction: string;
  scores: PredictionScore[];
}

export interface HistoryItem {
  id: number;
  filename: string;
  predicted_class: string;
  confidence: number;
  all_scores: Record<string, number>;
  created_at: string;
}

export async function predict(file: File): Promise<PredictionResult> {
  const form = new FormData();
  form.append("file", file);
  const res = await api.post<PredictionResult>("/predict", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  const d = res.data;
  // Normalise: add UI-friendly aliases
  const scores = (d.all_scores ?? []).map((s) => ({
    ...s,
    label: s.code,
    probability: s.confidence,
  }));
  return {
    ...d,
    prediction: d.predicted_class,
    scores,
  };
}

export async function getHistory(): Promise<HistoryItem[]> {
  const res = await api.get<HistoryItem[]>("/history");
  return res.data;
}

export async function getMetrics(): Promise<Record<string, unknown>> {
  const res = await api.get<Record<string, unknown>>("/metrics");
  return res.data;
}
