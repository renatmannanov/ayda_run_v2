import React from 'react'
import BottomNav from './BottomNav'

/**
 * BottomBar - unified fixed bottom container for action bar + navigation
 *
 * Usage:
 * <BottomBar
 *   action={<button>Записаться</button>}  // optional action component above nav
 *   showAction={true}                      // control action visibility
 *   onCreateClick={() => {}}               // passed to BottomNav
 * />
 *
 * Structure:
 * ┌─────────────────────────────────┐
 * │  [Action Bar - optional]        │
 * │  [Bottom Navigation]            │
 * └─────────────────────────────────┘
 */
export default function BottomBar({
    action,
    showAction = true,
    onCreateClick,
    canCreate = true
}) {
    return (
        <div className="fixed bottom-0 left-0 right-0 max-w-md mx-auto z-40">
            {/* Action Bar - above BottomNav */}
            {action && showAction && (
                <div className="bg-white border-t border-gray-200 px-4 py-2">
                    {action}
                </div>
            )}
            {/* Bottom Navigation */}
            <BottomNav onCreateClick={onCreateClick} canCreate={canCreate} />
        </div>
    )
}
