import axios from "axios";

// In Docker → nginx proxies /api → backend
// In dev (vite proxy) → /api → localhost:8000
const BASE_URL = "/api";

const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30_000,
});

// Attach JWT on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Logout automatically on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

export default api;
