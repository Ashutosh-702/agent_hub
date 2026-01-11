import { createContext, useContext, useState, useCallback, type ReactNode } from 'react';

type ToastType = 'success' | 'error' | 'warning' | 'info';

interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastContextType {
  showToast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within ToastProvider');
  }
  return context;
};

const toastStyles: Record<ToastType, { bg: string; border: string; icon: string }> = {
  success: { bg: '#ecfdf5', border: '#10b981', icon: '✓' },
  error: { bg: '#fef2f2', border: '#ef4444', icon: '✕' },
  warning: { bg: '#fffbeb', border: '#f59e0b', icon: '!' },
  info: { bg: '#eff6ff', border: '#3b82f6', icon: 'i' },
};

const ToastItem = ({ toast, onRemove }: { toast: Toast; onRemove: () => void }) => {
  const style = toastStyles[toast.type];

  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: '0.75rem',
        padding: '1rem 1.25rem',
        background: style.bg,
        border: `1px solid ${style.border}`,
        borderRadius: '10px',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.12)',
        animation: 'slideIn 0.3s ease',
        minWidth: '300px',
        maxWidth: '450px',
      }}
    >
      <div
        style={{
          width: '24px',
          height: '24px',
          borderRadius: '50%',
          background: style.border,
          color: 'white',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: '0.75rem',
          fontWeight: 700,
          flexShrink: 0,
        }}
      >
        {style.icon}
      </div>
      <p
        style={{
          margin: 0,
          fontSize: '0.9375rem',
          color: 'var(--color-gray-800)',
          fontWeight: 500,
          flex: 1,
        }}
      >
        {toast.message}
      </p>
      <button
        onClick={onRemove}
        style={{
          background: 'none',
          border: 'none',
          padding: '0.25rem',
          cursor: 'pointer',
          color: 'var(--color-gray-400)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: '4px',
          transition: 'all 0.15s ease',
        }}
        onMouseOver={(e) => {
          e.currentTarget.style.background = 'rgba(0, 0, 0, 0.05)';
          e.currentTarget.style.color = 'var(--color-gray-600)';
        }}
        onMouseOut={(e) => {
          e.currentTarget.style.background = 'none';
          e.currentTarget.style.color = 'var(--color-gray-400)';
        }}
        aria-label="Dismiss"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="18" y1="6" x2="6" y2="18" />
          <line x1="6" y1="6" x2="18" y2="18" />
        </svg>
      </button>
    </div>
  );
};

export const ToastProvider = ({ children }: { children: ReactNode }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = useCallback((message: string, type: ToastType = 'info') => {
    const id = Math.random().toString(36).substr(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);

    // Auto remove after 4 seconds
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      <div
        style={{
          position: 'fixed',
          bottom: '1.5rem',
          right: '1.5rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.75rem',
          zIndex: 9999,
        }}
      >
        {toasts.map((toast) => (
          <ToastItem key={toast.id} toast={toast} onRemove={() => removeToast(toast.id)} />
        ))}
      </div>
      <style>{`
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateX(100%);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
      `}</style>
    </ToastContext.Provider>
  );
};

// Also export a standalone Toast component for simple cases
export const Toast = ToastItem;


