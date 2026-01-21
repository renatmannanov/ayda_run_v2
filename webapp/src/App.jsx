import { Routes, Route, useNavigate } from 'react-router-dom'
import { useEffect } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { queryClient } from './queryClient'
import { UserProvider } from './contexts/UserContext'
import { ToastProvider } from './contexts/ToastContext'
import { useScreenTracking } from './hooks/useAnalytics'
import Home from './screens/Home'
import ActivityDetail from './screens/ActivityDetail'
import ActivityCreate from './screens/ActivityCreate'
import ClubsGroups from './screens/ClubsGroups'
import ClubGroupDetail from './screens/ClubGroupDetail'
import CreateClub from './screens/CreateClub'
import CreateGroup from './screens/CreateGroup'
import Profile from './screens/Profile'
import Statistics from './screens/Statistics'
import Settings from './screens/Settings'

function App() {
    const navigate = useNavigate()

    // Track screen views on route changes
    useScreenTracking()

    // Initialize Telegram WebApp and handle deep links
    useEffect(() => {
        if (window.Telegram?.WebApp) {
            window.Telegram.WebApp.ready()
            window.Telegram.WebApp.expand()

            // Disable pull-to-dismiss on iOS (available in Bot API 7.7+)
            if (window.Telegram.WebApp.disableVerticalSwipes) {
                window.Telegram.WebApp.disableVerticalSwipes()
            }

            // Handle deep link from start_param (e.g., ?startapp=activity_123)
            // This is a fallback for old-style links - new links use direct paths
            const urlParams = new URLSearchParams(window.location.search)
            const startappFromUrl = urlParams.get('startapp')
            const startParam = window.Telegram.WebApp.initDataUnsafe?.start_param || startappFromUrl

            if (startParam) {
                if (startParam.startsWith('activity_')) {
                    const activityId = startParam.replace('activity_', '')
                    navigate(`/activity/${activityId}`)
                } else if (startParam.startsWith('club_')) {
                    const clubId = startParam.replace('club_', '')
                    navigate(`/club/${clubId}`)
                } else if (startParam.startsWith('group_')) {
                    const groupId = startParam.replace('group_', '')
                    navigate(`/group/${groupId}`)
                }
            }
        }
    }, [navigate])

    return (
        <QueryClientProvider client={queryClient}>
            <UserProvider>
                <ToastProvider>
                    <div className="min-h-screen bg-gray-50 max-w-md mx-auto">
                        <Routes>
                        <Route path="/" element={<Home />} />
                        <Route path="/activity/:id" element={<ActivityDetail />} />
                        <Route path="/activity/:id/edit" element={<ActivityCreate />} />
                        <Route path="/activity/create" element={<ActivityCreate />} />
                        <Route path="/clubs" element={<ClubsGroups />} />
                        <Route path="/club/:id" element={<ClubGroupDetail type="club" />} />
                        <Route path="/club/:id/edit" element={<CreateClub />} />
                        <Route path="/group/:id" element={<ClubGroupDetail type="group" />} />
                        <Route path="/group/:id/edit" element={<CreateGroup />} />
                        <Route path="/club/create" element={<CreateClub />} />
                        <Route path="/group/create" element={<CreateGroup />} />
                        <Route path="/profile" element={<Profile />} />
                        <Route path="/statistics" element={<Statistics />} />
                        <Route path="/settings" element={<Settings />} />
                        </Routes>
                    </div>
                </ToastProvider>
            </UserProvider>
            <ReactQueryDevtools initialIsOpen={false} />
        </QueryClientProvider>
    )
}

export default App
