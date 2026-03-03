import { useState, useEffect, createContext, useContext, useCallback } from 'react';
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-react';

const ToastContext = createContext(null);

const ICONS = {
    success: CheckCircle,
    error: XCircle,
    warning: AlertTriangle,
    info: Info,
};

const STYLES = {
    success: 'bg-white border-emerald-200 text-emerald-800',
    error: 'bg-white border-red-200 text-red-800',
    warning: 'bg-white border-amber-200 text-amber-800',
    info: 'bg-white border-indigo-200 text-indigo-800',
};

const ICON_COLORS = {
    success: 'text-emerald-500',
    error: 'text-red-500',
    warning: 'text-amber-500',
    info: 'text-indigo-500',
};

function ToastItem({ toast, onRemove }) {
    const Icon = ICONS[toast.type] || Info;

    useEffect(() => {
        const timer = setTimeout(() => onRemove(toast.id), toast.duration || 4000);
        return () => clearTimeout(timer);
    }, [toast.id, toast.duration, onRemove]);

    return (
        <div className={`flex items-start gap-3 p-4 rounded-xl border shadow-lg shadow-black/5 max-w-sm w-full ${STYLES[toast.type]} animate-in slide-in-from-right-4 duration-300`}>
            <Icon size={18} className={`shrink-0 mt-0.5 ${ICON_COLORS[toast.type]}`} />
            <div className="flex-1 min-w-0">
                {toast.title && <div className="font-semibold text-sm">{toast.title}</div>}
                <div className={`text-sm ${toast.title ? 'text-gray-600 mt-0.5' : 'font-medium'}`}>{toast.message}</div>
            </div>
            <button
                onClick={() => onRemove(toast.id)}
                className="shrink-0 text-gray-300 hover:text-gray-600 transition-colors"
            >
                <X size={16} />
            </button>
        </div>
    );
}

export function ToastProvider({ children }) {
    const [toasts, setToasts] = useState([]);

    const removeToast = useCallback((id) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    }, []);

    const addToast = useCallback(({ type = 'info', title, message, duration = 4000 }) => {
        const id = Date.now() + Math.random();
        setToasts(prev => [...prev.slice(-4), { id, type, title, message, duration }]);
    }, []);

    const toast = {
        success: (message, title) => addToast({ type: 'success', message, title }),
        error: (message, title) => addToast({ type: 'error', message, title, duration: 6000 }),
        warning: (message, title) => addToast({ type: 'warning', message, title }),
        info: (message, title) => addToast({ type: 'info', message, title }),
    };

    return (
        <ToastContext.Provider value={toast}>
            {children}
            <div className="fixed bottom-6 right-6 z-[9999] flex flex-col gap-3">
                {toasts.map(t => (
                    <ToastItem key={t.id} toast={t} onRemove={removeToast} />
                ))}
            </div>
        </ToastContext.Provider>
    );
}

export function useToast() {
    const ctx = useContext(ToastContext);
    if (!ctx) throw new Error('useToast must be used within ToastProvider');
    return ctx;
}
