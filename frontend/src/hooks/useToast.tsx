import {
  createContext,
  useCallback,
  useContext,
  useId,
  useState,
} from "react";
import { createUserNotification } from "../api/notifications";
import { NOTIFICATIONS_REFRESH_EVENT } from "../constants/notificationsEvents";

type ToastVariant = "success" | "error";

export type ShowToastOptions = { persist?: boolean };

type ToastItem = {
  id: string;
  message: string;
  variant: ToastVariant;
};

type ToastContextValue = {
  showToast: (message: string, variant?: ToastVariant, options?: ShowToastOptions) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const baseId = useId();
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const showToast = useCallback(
    (message: string, variant: ToastVariant = "error", options?: ShowToastOptions) => {
      const id = `${baseId}-${Date.now()}`;
      setToasts((prev) => [...prev, { id, message, variant }]);
      window.setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 4500);
      if (options?.persist) {
        const level = variant === "success" ? "success" : "error";
        void createUserNotification({ level, title: message, body: "" })
          .then(() => {
            window.dispatchEvent(new Event(NOTIFICATIONS_REFRESH_EVENT));
          })
          .catch(() => {});
      }
    },
    [baseId],
  );

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div className="toast-stack" aria-live="polite" aria-relevant="additions">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`toast toast-${t.variant}`}
            role="status"
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast deve ser usado dentro de ToastProvider");
  }
  return ctx;
}
