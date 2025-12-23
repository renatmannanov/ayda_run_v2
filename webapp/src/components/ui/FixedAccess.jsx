import React from 'react'

export default function FixedAccess({ icon, label, hint }) {
    return (
        <div>
            <div className="flex gap-2">
                <div className="flex items-center gap-2 px-4 py-2.5 rounded-full text-sm bg-gray-800 text-white">
                    {icon && <span>{icon}</span>}
                    <span>{label}</span>
                </div>
            </div>
            {hint && <p className="text-xs text-gray-400 mt-2">{hint}</p>}
        </div>
    )
}
