import React, { createContext, useCallback, useContext, useRef, useState } from "react";

export type ToastType = "success" | "error" | "info";

export interface Toast {
  id: number;
  type: ToastType;
  message: string;
}

interface ToastContextValue {
  toast: (type: ToastType, message: string, duration?: number) => void;
  success: (message: string) => void;
  error: (message: string) => void;
  info: (message: string) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used inside ToastProvider");
  return ctx;
}

const ICONS: Record<ToastType, string> = {
  success: "✓",
  error:   "✕",
  info:    "ℹ",
};

const STYLES: Record<ToastType, string> = {
  success: "bg-emerald-600 text-white",
  error:   "bg-red-600   text-white",
  info:    "bg-brand-600  text-white",
};

function ToastItem({ toast, onDismiss }: { toast: Toast; onDismiss: (id: number) => void }) {
  return (
    <div
      className={`flex items-start gap-3 min-w-[280px] max-w-sm w-full rounded-xl shadow-lg px-4 py-3 pointer-events-auto
        animate-toast-in ${STYLES[toast.type]}`}
      role="alert"
    >
      <span className="mt-0.5 text-base font-bold shrink-0 w-5 h-5 flex items-center justify-center
        bg-white/20 rounded-full text-xs">
        {ICONS[toast.type]}
      </span>
      <p className="flex-1 text-sm font-medium leading-snug">{toast.message}</p>
      <button
        onClick={() => onDismiss(toast.id)}
        className="shrink-0 opacity-70 hover:opacity-100 transition-opacity text-sm mt-0.5"
        aria-label="Dismiss"
      >
        ✕
      </button>
    </div>
  );
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const counterRef = useRef(0);

  const dismiss = useCallback((id: number) => {
    setToasts((t) => t.filter((x) => x.id !== id));
  }, []);

  const toast = useCallback((type: ToastType, message: string, duration = 4000) => {
    const id = ++counterRef.current;
    setToasts((t) => [...t, { id, type, message }]);
    setTimeout(() => dismiss(id), duration);
  }, [dismiss]);

  const success = useCallback((msg: string) => toast("success", msg), [toast]);
  const error   = useCallback((msg: string) => toast("error",   msg, 6000), [toast]);
  const info    = useCallback((msg: string) => toast("info",    msg), [toast]);

  return (
    <ToastContext.Provider value={{ toast, success, error, info }}>
      {children}
      {/* bottom-end corner — flips automatically in RTL */}
      <div className="fixed bottom-5 end-5 z-[9999] flex flex-col gap-2.5 items-end rtl:items-start pointer-events-none">
        {toasts.map((t) => (
          <ToastItem key={t.id} toast={t} onDismiss={dismiss} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}
