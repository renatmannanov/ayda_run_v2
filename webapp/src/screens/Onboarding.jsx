import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { SportChips, Button } from '../components'
import { tg } from '../api'

export default function Onboarding() {
    const navigate = useNavigate()
    const [step, setStep] = useState(1)
    const [selectedSports, setSelectedSports] = useState([])

    const user = tg.user || { first_name: 'Бегун' }

    // Invite context (if came from invite link)
    // TODO: parse start_param from TG
    const inviteContext = null

    // Complete onboarding
    const completeOnboarding = () => {
        // TODO: Send selected sports to API if profile update supported
        // await usersApi.update({ sports: selectedSports })
        navigate('/')
    }

    // Step 1: Welcome
    const Step1 = () => (
        <div className="flex-1 flex flex-col items-center justify-center px-6 text-center">
            <span className="text-6xl mb-6">🏃</span>
            <h1 className="text-2xl text-gray-800 font-medium mb-3">
                Привет, {user.first_name}!
            </h1>
            <p className="text-base text-gray-500 mb-8 max-w-xs">
                Ayda Run — твой помощник для тренировок в беговых клубах
            </p>
            <div className="w-full max-w-xs">
                <Button onClick={() => setStep(2)}>
                    Начать
                </Button>
            </div>
        </div>
    )

    // Step 2: Sport Selection
    const Step2 = () => (
        <div className="flex-1 flex flex-col px-6 pt-12">
            <div className="mb-8">
                <h1 className="text-xl text-gray-800 font-medium mb-2">
                    Чем занимаешься?
                </h1>
                <p className="text-sm text-gray-500">
                    Выбери один или несколько видов спорта
                </p>
            </div>

            <div className="mb-auto">
                <SportChips
                    selected={selectedSports}
                    onChange={setSelectedSports}
                    multiple={true}
                    label=""
                />
            </div>

            <div className="py-6">
                <Button
                    onClick={() => setStep(3)}
                    disabled={selectedSports.length === 0}
                >
                    Продолжить
                </Button>
            </div>
        </div>
    )

    // Step 3: Ready
    const Step3 = () => (
        <div className="flex-1 flex flex-col items-center justify-center px-6 text-center">
            <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mb-6">
                <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
            </div>

            <h1 className="text-xl text-gray-800 font-medium mb-2">
                Готово!
            </h1>
            <p className="text-sm text-gray-500 mb-8 max-w-xs">
                Теперь можешь записываться на тренировки и следить за расписанием
            </p>

            {inviteContext && (
                <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 mb-6 w-full max-w-xs">
                    <p className="text-xs text-gray-400 mb-1">Тебя пригласили в</p>
                    <p className="text-sm text-gray-800 font-medium">{inviteContext.name}</p>
                </div>
            )}

            <div className="w-full max-w-xs">
                <Button onClick={completeOnboarding}>
                    {inviteContext ? 'Перейти в клуб' : 'Перейти к тренировкам'}
                </Button>
            </div>
        </div>
    )

    // Progress dots
    const ProgressDots = () => (
        <div className="flex justify-center gap-2 py-4">
            {[1, 2, 3].map(s => (
                <div
                    key={s}
                    className={`w-2 h-2 rounded-full transition-colors ${s === step ? 'bg-gray-800' : 'bg-gray-200'
                        }`}
                />
            ))}
        </div>
    )

    return (
        <div className="min-h-screen bg-white flex flex-col">
            {/* Skip button (steps 1-2) */}
            {step < 3 && (
                <div className="flex justify-end px-4 py-4">
                    <button
                        onClick={completeOnboarding}
                        className="text-sm text-gray-400 hover:text-gray-600 transition-colors"
                    >
                        Пропустить
                    </button>
                </div>
            )}

            {/* Content */}
            {step === 1 && <Step1 />}
            {step === 2 && <Step2 />}
            {step === 3 && <Step3 />}

            {/* Progress */}
            <ProgressDots />
        </div>
    )
}
