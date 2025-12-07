import { Routes, Route } from 'react-router-dom'
import { useEffect } from 'react'
import Home from './screens/Home'
import ActivityDetail from './screens/ActivityDetail'
import ActivityCreate from './screens/ActivityCreate'
import ClubsGroups from './screens/ClubsGroups'
import ClubGroupDetail from './screens/ClubGroupDetail'
import CreateClub from './screens/CreateClub'
import CreateGroup from './screens/CreateGroup'
import Profile from './screens/Profile'
import Onboarding from './screens/Onboarding'

function App() {
    // Initialize Telegram WebApp
    useEffect(() => {
        if (window.Telegram?.WebApp) {
            window.Telegram.WebApp.ready()
            window.Telegram.WebApp.expand()
        }
    }, [])

    return (
        <div className="min-h-screen bg-gray-50 max-w-md mx-auto">
            <Routes>
                <Route path="/" element={<Home />} />
                <Route path="/activity/:id" element={<ActivityDetail />} />
                <Route path="/activity/create" element={<ActivityCreate />} />
                <Route path="/clubs" element={<ClubsGroups />} />
                <Route path="/club/:id" element={<ClubGroupDetail type="club" />} />
                <Route path="/group/:id" element={<ClubGroupDetail type="group" />} />
                <Route path="/club/create" element={<CreateClub />} />
                <Route path="/group/create" element={<CreateGroup />} />
                <Route path="/profile" element={<Profile />} />
                <Route path="/onboarding" element={<Onboarding />} />
            </Routes>
        </div>
    )
}

export default App
