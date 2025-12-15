import { Routes, Route, useNavigate, useLocation } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { queryClient } from './queryClient'
import Home from './screens/Home'
import ActivityDetail from './screens/ActivityDetail'
import ActivityCreate from './screens/ActivityCreate'
import ClubsGroups from './screens/ClubsGroups'
import ClubGroupDetail from './screens/ClubGroupDetail'
import CreateClub from './screens/CreateClub'
import CreateGroup from './screens/CreateGroup'
import Profile from './screens/Profile'
import Onboarding from './screens/Onboarding'
import { api } from './api'

function App() {
    const navigate = useNavigate()
    const location = useLocation()
    const [checkingOnboarding, setCheckingOnboarding] = useState(true)

    // Initialize Telegram WebApp
    useEffect(() => {
        if (window.Telegram?.WebApp) {
            window.Telegram.WebApp.ready()
            window.Telegram.WebApp.expand()
        }
    }, [])

    // Check onboarding status
    useEffect(() => {
        const checkOnboarding = async () => {
            // Don't check if already on onboarding page
            if (location.pathname === '/onboarding') {
                setCheckingOnboarding(false)
                return
            }

            try {
                const user = await api.get('/users/me')

                // Redirect to onboarding if not completed
                if (!user.has_completed_onboarding) {
                    navigate('/onboarding')
                }
            } catch (error) {
                console.error('Failed to check onboarding status:', error)
                // Don't block user on error
            } finally {
                setCheckingOnboarding(false)
            }
        }

        checkOnboarding()
    }, [navigate, location.pathname])

    // Show loading while checking onboarding
    if (checkingOnboarding) {
        return (
            <div className="min-h-screen bg-gray-50 flex items-center justify-center">
                <div className="text-gray-500">Загрузка...</div>
            </div>
        )
    }

    return (
        <QueryClientProvider client={queryClient}>
            <div className="min-h-screen bg-gray-50 max-w-md mx-auto">
                <Routes>
                    <Route path="/" element={<Home />} />
                    <Route path="/activity/:id" element={<ActivityDetail />} />
                    <Route path="/activity/create" element={<ActivityCreate />} />
                    <Route path="/clubs" element={<ClubsGroups />} />
                    <Route path="/club/:id" element={<ClubGroupDetail type="club" />} />
                    <Route path="/club/:id/edit" element={<CreateClub />} />
                    <Route path="/group/:id" element={<ClubGroupDetail type="group" />} />
                    <Route path="/group/:id/edit" element={<CreateGroup />} />
                    <Route path="/club/create" element={<CreateClub />} />
                    <Route path="/group/create" element={<CreateGroup />} />
                    <Route path="/profile" element={<Profile />} />
                    <Route path="/onboarding" element={<Onboarding />} />
                </Routes>
            </div>
            <ReactQueryDevtools initialIsOpen={false} />
        </QueryClientProvider>
    )
}

export default App
