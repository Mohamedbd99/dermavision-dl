import api from "./api";

export interface PredictionScore {
  label: string;
  probability: number;
  full_name: string;
}

export interface PredictionResult {
  prediction: string;
  confidence: number;
  scores: PredictionScore[];
}

export interface HistoryItem {
  id: number;
  filename: string;
  prediction: string;
  confidence: number;
  created_at: string;
}

export async function predict(file: File): Promise<PredictionResult> {
  const form = new FormData();
  form.append("file", file);
  const res = await api.post<PredictionResult>("/predict", form, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

export async function getHistory(): Promise<HistoryItem[]> {
  const res = await api.get<HistoryItem[]>("/history");
  return res.data;
}

export async function getMetrics(): Promise<Record<string, unknown>> {
  const res = await api.get<Record<string, unknown>>("/metrics");
  return res.data;
}
