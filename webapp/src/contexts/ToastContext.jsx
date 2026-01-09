import React, { createContext, useContext, useState, useCallback } from 'react'

const ToastContext = createContext(null)

export function ToastProvider({ children }) {
    const [toast, setToast] = useState(null)

    const showToast = useCallback((message, type = 'success') => {
        setToast({ message, type })
        // Auto-hide after 2 seconds
        setTimeout(() => setToast(null), 2000)
    }, [])

    const hideToast = useCallback(() => {
        setToast(null)
    }, [])

    return (
        <ToastContext.Provider value={{ showToast, hideToast }}>
            {children}
            {toast && (
                <Toast
                    message={toast.message}
                    type={toast.type}
                    onClose={hideToast}
                />
            )}
        </ToastContext.Provider>
    )
}

export function useToast() {
    const context = useContext(ToastContext)
    if (!context) {
        throw new Error('useToast must be used within ToastProvider')
    }
    return context
}

// Toast component - positioned exactly at action bar level (above BottomNav)
function Toast({ message, type = 'success', onClose }) {
    const styles = {
        success: 'border-green-600 text-green-600',
        info: 'border-gray-400 text-gray-600',
        error: 'border-red-600 text-red-600',
        warning: 'border-orange-500 text-orange-600'
    }

    // bottom-[65px] = aligned with action bar position
    // h-12 = 48px = unified height for all action bar elements
    return (
        <div className="fixed bottom-[65px] left-0 right-0 z-50">
            <div className="max-w-md mx-auto px-4 py-2 bg-white border-t border-gray-200">
                <div
                    className={`w-full h-12 bg-white border-2 ${styles[type]} rounded-xl px-4 flex items-center justify-center cursor-pointer`}
                    onClick={onClose}
                >
                    <span className="text-sm font-medium">{message}</span>
                </div>
            </div>
        </div>
    )
}
