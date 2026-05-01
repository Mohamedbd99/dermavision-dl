/**
 * Converts a FastAPI / axios error into a human-readable string.
 *
 * FastAPI validation errors look like:
 *   { detail: [ { msg: "Value error, password must be…", loc: ["body","password"] } ] }
 *
 * Auth errors look like:
 *   { detail: "Incorrect username or password" }
 *
 * Network errors have no response at all.
 */

type FastApiValidationError = { msg?: string; loc?: string[] };

interface AxiosLikeError {
  response?: {
    data?: {
      detail?: string | FastApiValidationError[];
    };
    status?: number;
  };
  message?: string;
}

export function parseApiError(err: unknown, fallback = "Something went wrong. Please try again."): string {
  const e = err as AxiosLikeError;
  const detail = e?.response?.data?.detail;

  // Array of FastAPI validation errors
  if (Array.isArray(detail)) {
    return detail
      .map((d) => {
        const field = d.loc ? d.loc.filter((l) => l !== "body").join(" → ") : "";
        // strip the "Value error, " prefix FastAPI sometimes adds
        const msg   = (d.msg ?? "Invalid value").replace(/^value error,\s*/i, "");
        return field ? `${field}: ${msg}` : msg;
      })
      .join("\n");
  }

  // Plain string detail
  if (typeof detail === "string" && detail.trim()) {
    return detail;
  }

  // Network / unknown error
  if (e?.message) return e.message;

  return fallback;
}
