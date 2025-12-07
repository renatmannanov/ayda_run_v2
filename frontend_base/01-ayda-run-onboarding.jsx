import React, { useState } from 'react';

// Simulated Telegram user data
const telegramUser = {
  first_name: "Ренат",
  username: "renat_run",
  id: 123456789
};

// Simulated invite context (null = generic, string = club name)
const inviteContext = null; // or "SRG Almaty"

const sportTypes = [
  { id: 'running', icon: '🏃', label: 'Бег' },
  { id: 'trail', icon: '⛰️', label: 'Трейл' },
  { id: 'hiking', icon: '🥾', label: 'Хайкинг' },
  { id: 'cycling', icon: '🚴', label: 'Вело' }
];

export default function AydaRunOnboarding() {
  const [step, setStep] = useState(1);
  const [selectedSports, setSelectedSports] = useState([]);
  const [isCompleted, setIsCompleted] = useState(false);

  const toggleSport = (sportId) => {
    setSelectedSports(prev => 
      prev.includes(sportId) 
        ? prev.filter(id => id !== sportId)
        : [...prev, sportId]
    );
  };

  const handleNext = () => {
    if (step < 3) {
      setStep(step + 1);
    } else {
      setIsCompleted(true);
    }
  };

  const handleSkip = () => {
    setStep(step + 1);
  };

  // Step 1: Welcome
  const WelcomeStep = () => (
    <div className="flex-1 flex flex-col items-center justify-center px-8 text-center">
      <div className="text-6xl mb-6">🏃</div>
      <h1 className="text-xl text-gray-800 font-medium mb-3">
        Привет, {telegramUser.first_name}!
      </h1>
      <p className="text-gray-500 text-base leading-relaxed mb-8">
        Ayda Run — простой способ<br />
        следить за тренировками<br />
        твоего клуба
      </p>
    </div>
  );

  // Step 2: Sport Preference
  const SportStep = () => (
    <div className="flex-1 flex flex-col px-6 pt-12">
      <h2 className="text-lg text-gray-800 font-medium mb-8 text-center">
        Что тебе ближе?
      </h2>
      
      <div className="grid grid-cols-2 gap-3 mb-6">
        {sportTypes.map(sport => (
          <button
            key={sport.id}
            onClick={() => toggleSport(sport.id)}
            className={`
              py-5 px-4 rounded-xl border-2 transition-all duration-200
              flex flex-col items-center gap-2
              ${selectedSports.includes(sport.id)
                ? 'border-gray-800 bg-gray-50'
                : 'border-gray-200 bg-white hover:border-gray-300'
              }
            `}
          >
            <span className="text-3xl">{sport.icon}</span>
            <span className={`text-sm ${
              selectedSports.includes(sport.id) 
                ? 'text-gray-800 font-medium' 
                : 'text-gray-600'
            }`}>
              {sport.label}
            </span>
          </button>
        ))}
      </div>
      
      <p className="text-gray-400 text-sm text-center">
        Можно выбрать несколько
      </p>
    </div>
  );

  // Step 3: Completion
  const CompletionStep = () => (
    <div className="flex-1 flex flex-col items-center justify-center px-8 text-center">
      <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mb-6">
        <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      </div>
      
      <h1 className="text-xl text-gray-800 font-medium mb-3">
        Ты в деле!
      </h1>
      
      {inviteContext ? (
        <p className="text-gray-500 text-base leading-relaxed">
          Тебя ждут в<br />
          <span className="text-gray-800 font-medium">{inviteContext}</span>
        </p>
      ) : (
        <p className="text-gray-500 text-base leading-relaxed">
          Найди единомышленников<br />
          или организуй свою активность
        </p>
      )}
    </div>
  );

  // Completed state (would redirect to Home)
  if (isCompleted) {
    return (
      <div className="min-h-screen bg-white flex flex-col items-center justify-center max-w-md mx-auto">
        <div className="text-4xl mb-4">✨</div>
        <p className="text-gray-600">Redirecting to Home...</p>
        <button 
          onClick={() => {
            setStep(1);
            setSelectedSports([]);
            setIsCompleted(false);
          }}
          className="mt-4 text-sm text-gray-400 hover:text-gray-600"
        >
          Reset demo
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white flex flex-col max-w-md mx-auto">
      {/* Progress indicator */}
      <div className="px-6 pt-6">
        <div className="flex gap-2">
          {[1, 2, 3].map(i => (
            <div 
              key={i}
              className={`h-1 flex-1 rounded-full transition-colors duration-300 ${
                i <= step ? 'bg-gray-800' : 'bg-gray-200'
              }`}
            />
          ))}
        </div>
      </div>

      {/* Content */}
      {step === 1 && <WelcomeStep />}
      {step === 2 && <SportStep />}
      {step === 3 && <CompletionStep />}

      {/* Actions */}
      <div className="px-6 pb-8">
        {step === 2 ? (
          <div className="flex items-center justify-between">
            <button
              onClick={handleSkip}
              className="text-gray-400 text-sm hover:text-gray-600 transition-colors"
            >
              Пропустить
            </button>
            <button
              onClick={handleNext}
              disabled={selectedSports.length === 0}
              className={`
                px-6 py-3 rounded-xl text-sm font-medium transition-all
                ${selectedSports.length > 0
                  ? 'bg-gray-800 text-white hover:bg-gray-700'
                  : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                }
              `}
            >
              Готово
            </button>
          </div>
        ) : (
          <button
            onClick={handleNext}
            className="w-full py-4 bg-gray-800 text-white rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors"
          >
            {step === 1 ? 'Начать' : (inviteContext ? `Перейти в ${inviteContext}` : 'Поехали')}
          </button>
        )}
      </div>
    </div>
  );
}
