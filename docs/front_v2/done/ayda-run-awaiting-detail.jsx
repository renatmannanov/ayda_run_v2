import React, { useState } from 'react';

// Sample activity data
const sampleActivity = {
  id: 1,
  title: "Длинная в горы",
  organizer: { type: 'club', club: "SRG Almaty", group: "Горные бегуны" },
  date: "сб, 27 дек",
  time: "07:00",
  location: "Медеу, старт у касс",
  distance: "10 км",
  elevation: "850 м",
  sportIcon: "⛰️",
  participants: 8,
  maxParticipants: 20,
  status: 'none',
  isPrivate: false,
  hasGpx: true,
  description: "Берите с собой воду и гели. Обязательно трейловые кроссовки! Набор высоты серьёзный. Темп комфортный, никого не бросаем."
};

const sampleActivityUser = {
  id: 2,
  title: "Вечерний бег в парке",
  organizer: { type: 'user', name: "Марат", avatar: "👨" },
  date: "вт, 24 дек",
  time: "19:00",
  location: "Центральный парк, главный вход",
  distance: "5 км",
  elevation: null,
  sportIcon: "🏃",
  participants: 3,
  maxParticipants: 10,
  status: 'none',
  isPrivate: false,
  hasGpx: false,
  description: "Лёгкая пробежка по парку. Темп разговорный. Подходит для начинающих."
};

const sampleActivityPrivate = {
  id: 3,
  title: "Закрытая тренировка",
  organizer: { type: 'club', club: "Trail Nomads", group: "Продвинутые" },
  date: "сб, 27 дек",
  time: "06:00",
  location: "Бутаковка",
  distance: "15 км",
  elevation: "1200 м",
  sportIcon: "🥾",
  participants: 4,
  maxParticipants: 12,
  status: 'none',
  isPrivate: true,
  hasGpx: true,
  description: "Только для участников группы. Серьёзный набор, нужен опыт горного бега."
};

const sampleActivityAwaiting = {
  id: 4,
  title: "Утренняя йога",
  organizer: { type: 'club', club: "Yoga Club", group: "Начинающие" },
  date: "пн, 23 дек",
  time: "08:00",
  location: "Студия Zen",
  distance: null,
  elevation: null,
  sportIcon: "🧘",
  participants: 5,
  maxParticipants: 15,
  status: 'awaiting',
  isPrivate: false,
  hasGpx: false,
  description: "Мягкая утренняя практика. Подходит для любого уровня."
};

const sampleParticipants = [
  { id: 1, name: "Анна", avatar: "👩", isOrganizer: true, sports: ["🏃", "⛰️"], stravaUrl: "https://strava.com/athletes/anna" },
  { id: 2, name: "Марат", avatar: "👨", isOrganizer: false, sports: ["🏃", "🚴"], stravaUrl: "https://strava.com/athletes/marat" },
  { id: 3, name: "Дима", avatar: "👦", isOrganizer: false, sports: ["🏃"], stravaUrl: null },
  { id: 4, name: "Алия", avatar: "👩", isOrganizer: false, sports: ["🏃", "⛰️", "🥾"], stravaUrl: "https://strava.com/athletes/aliya" },
  { id: 5, name: "Саша", avatar: "👨", isOrganizer: false, sports: ["🏃"], stravaUrl: null },
  { id: 6, name: "Женя", avatar: "👩", isOrganizer: false, sports: ["⛰️"], stravaUrl: "https://strava.com/athletes/zhenya" },
  { id: 7, name: "Костя", avatar: "👨", isOrganizer: false, sports: ["🏃", "🚴"], stravaUrl: null },
  { id: 8, name: "Лена", avatar: "👩", isOrganizer: false, sports: ["🧘"], stravaUrl: null },
];

// Strava Icon Component
const StravaIcon = ({ url }) => {
  if (!url) return <div className="w-6" />; // Placeholder for alignment
  return (
    <a 
      href={url}
      target="_blank"
      rel="noopener noreferrer"
      onClick={(e) => e.stopPropagation()}
      className="w-6 h-6 rounded bg-orange-500 flex items-center justify-center text-white text-xs font-bold hover:bg-orange-600 transition-colors flex-shrink-0"
    >
      S
    </a>
  );
};

// Participants Popup Component - Updated layout, appears above action button
const ParticipantsPopup = ({ participants, total, max, onClose, actionButton }) => (
  <div 
    className="fixed inset-0 bg-black/30 z-50 flex flex-col justify-end"
    onClick={onClose}
  >
    <div 
      className="bg-white w-full max-w-md mx-auto rounded-t-2xl flex flex-col"
      onClick={e => e.stopPropagation()}
      style={{ maxHeight: '50vh' }}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-4 border-b border-gray-200">
        <span className="text-base font-medium text-gray-800">Участники · {total}/{max}</span>
        <button onClick={onClose} className="text-gray-400 text-xl hover:text-gray-600">✕</button>
      </div>
      
      {/* Participants List */}
      <div className="flex-1 overflow-auto px-4 py-2">
        {participants.length === 0 ? (
          <div className="py-8 text-center text-sm text-gray-400">
            Пока никто не записался
          </div>
        ) : (
          participants.map(p => (
            <div key={p.id} className="flex items-center py-3 border-b border-gray-100 last:border-0">
              {/* Avatar */}
              <span className="text-2xl mr-3 flex-shrink-0">{p.avatar}</span>
              
              {/* Name + Sports - left side */}
              <div className="flex items-center gap-2 flex-1 min-w-0">
                <span className="text-sm text-gray-700">{p.name}</span>
                
                {/* Sports */}
                <div className="flex gap-0.5 flex-shrink-0">
                  {p.sports.map((sport, i) => (
                    <span key={i} className="text-sm">{sport}</span>
                  ))}
                </div>
              </div>
              
              {/* Organizer badge - right side near Strava */}
              {p.isOrganizer && (
                <span className="text-xs text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded mr-2 flex-shrink-0">Орг</span>
              )}
              
              {/* Strava - right aligned */}
              <StravaIcon url={p.stravaUrl} />
            </div>
          ))
        )}
      </div>
    </div>
    
    {/* Action Button Area - stays visible below popup */}
    <div className="bg-white w-full max-w-md mx-auto px-4 pb-6 pt-4 border-t border-gray-200">
      {actionButton}
    </div>
  </div>
);

// Activity Detail Component
const ActivityDetail = ({ activity, isOrganizer = false }) => {
  const [showParticipants, setShowParticipants] = useState(false);
  const [status, setStatus] = useState(activity.status);
  
  const getOrganizerDisplay = () => {
    if (activity.organizer.type === 'user') {
      return (
        <p className="text-sm text-gray-700 flex items-center gap-1">
          <span className="text-gray-400">организатор</span>
          <span className="text-xl cursor-pointer hover:opacity-70">{activity.organizer.avatar}</span>
          <span className="cursor-pointer hover:underline">{activity.organizer.name}</span>
        </p>
      );
    }
    return (
      <p className="text-sm text-gray-700">
        <span className="cursor-pointer hover:underline">🏆 {activity.organizer.club}</span>
        <span className="text-gray-400"> / </span>
        <span className="cursor-pointer hover:underline">{activity.organizer.group}</span>
      </p>
    );
  };

  const handleRegister = () => {
    setStatus('registered');
  };

  const handleCancel = () => {
    setStatus('none');
  };

  const handleShare = () => {
    navigator.clipboard.writeText(`https://t.me/aydarun_bot?start=activity_${activity.id}`);
    alert('Ссылка скопирована!');
  };

  const handleRequestAccess = () => {
    setStatus('pending');
  };

  const handleConfirmAttended = () => {
    setStatus('attended');
  };

  const handleConfirmMissed = () => {
    setStatus('missed');
  };

  // Get action button content (used in both bottom bar and popup)
  const getActionButton = () => {
    // Awaiting confirmation - show two buttons
    if (status === 'awaiting') {
      return (
        <div className="flex items-center gap-3">
          <button 
            onClick={handleConfirmMissed}
            className="flex-1 py-4 border border-gray-300 text-gray-500 rounded-xl text-sm font-medium hover:bg-gray-50 transition-colors"
          >
            Пропустил
          </button>
          <button 
            onClick={handleConfirmAttended}
            className="flex-1 py-4 bg-gray-800 text-white rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors"
          >
            Участвовал
          </button>
        </div>
      );
    }

    // Attended - show confirmation
    if (status === 'attended') {
      return (
        <div className="flex items-center justify-center gap-2 text-green-600">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
          </svg>
          <span className="text-sm font-medium">Участвовал</span>
        </div>
      );
    }

    // Missed - show confirmation
    if (status === 'missed') {
      return (
        <div className="flex items-center justify-center gap-2 text-gray-400">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
          <span className="text-sm font-medium">Пропустил</span>
        </div>
      );
    }

    // Private & not registered
    if (activity.isPrivate && status === 'none') {
      return (
        <button 
          onClick={handleRequestAccess}
          className="w-full py-4 bg-gray-800 text-white rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors flex items-center justify-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
          <span>Подать заявку на участие</span>
        </button>
      );
    }

    // Private & pending
    if (activity.isPrivate && status === 'pending') {
      return (
        <div className="flex items-center justify-between">
          <button 
            onClick={handleCancel}
            className="text-sm text-gray-400 hover:text-gray-600 transition-colors"
          >
            Отменить
          </button>
          <div className="flex items-center gap-2 text-gray-800">
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            <span className="text-sm font-medium">Заявка отправлена</span>
          </div>
        </div>
      );
    }

    // Not registered
    if (status === 'none') {
      return (
        <button 
          onClick={handleRegister}
          className="w-full py-4 bg-gray-800 text-white rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors"
        >
          Записаться
        </button>
      );
    }

    // Registered
    return (
      <div className="flex items-center justify-between">
        <button 
          onClick={handleCancel}
          className="text-sm text-gray-400 hover:text-gray-600 transition-colors"
        >
          Отменить
        </button>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-800 font-medium">Иду!</span>
          <button 
            onClick={handleShare}
            className="w-10 h-10 border border-gray-200 rounded-xl flex items-center justify-center text-gray-500 hover:bg-gray-50 transition-colors"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z" />
            </svg>
          </button>
        </div>
      </div>
    );
  };

  // Bottom action bar (when popup is closed)
  const renderBottomBar = () => {
    return (
      <div className="px-4 pb-6 pt-4 border-t border-gray-200 bg-white">
        {getActionButton()}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col max-w-md mx-auto">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-4">
        <button className="text-gray-500 text-sm hover:text-gray-700">
          ← Назад
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto px-4 py-4">
        <div className="bg-white border border-gray-200 rounded-xl p-4">
          {/* Title + Icon */}
          <div className="flex items-start justify-between mb-4">
            <h1 className="text-xl text-gray-800 font-medium">{activity.title}</h1>
            <span className="text-2xl ml-2">{activity.sportIcon}</span>
          </div>

          {/* Characteristics */}
          <div className="space-y-2 mb-2">
            <div className="flex items-center gap-3">
              <span className="text-base">📅</span>
              <span className="text-sm text-gray-700">{activity.date}, {activity.time}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className="text-base">📍</span>
              <span className="text-sm text-gray-700">{activity.location}</span>
            </div>
            {(activity.distance || activity.elevation) && (
              <div className="flex items-center gap-3">
                <span className="text-base">🏃</span>
                <span className="text-sm text-gray-700">
                  {[activity.distance, activity.elevation && `↗ ${activity.elevation}`].filter(Boolean).join(' · ')}
                </span>
              </div>
            )}
          </div>

          {/* GPX Download */}
          {activity.hasGpx && (
            <div className="mt-3 mb-2">
              <button className="text-xs text-gray-500 underline hover:text-gray-700 transition-colors">
                Скачать gpx трек
              </button>
            </div>
          )}

          <div className="border-t border-gray-200 my-4" />

          {/* Description */}
          <p className="text-sm text-gray-600 leading-relaxed">
            {activity.description}
          </p>

          <div className="border-t border-gray-200 my-4" />

          {/* Organizer */}
          <div className="mb-3">
            {getOrganizerDisplay()}
          </div>

          {/* Participants */}
          <button 
            onClick={() => setShowParticipants(true)}
            className="flex items-center gap-2 hover:opacity-70 transition-opacity"
          >
            <div className="flex -space-x-1">
              {sampleParticipants.slice(0, Math.min(8, activity.participants)).map(p => (
                <span key={p.id} className="text-xl">{p.avatar}</span>
              ))}
              {activity.participants === 0 && (
                <div className="w-7 h-7 rounded-full border-2 border-dashed border-gray-300" />
              )}
            </div>
            <span className="text-sm text-gray-500 ml-2">
              {activity.participants}/{activity.maxParticipants}
            </span>
          </button>

          {/* Organizer actions - moved to bottom */}
          {isOrganizer && (
            <>
              <div className="border-t border-gray-200 my-4" />
              <div className="space-y-2">
                {!activity.hasGpx && (
                  <button className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-900 transition-colors py-1">
                    <span>⚡</span>
                    <span className="font-medium">Добавить GPX файл</span>
                  </button>
                )}
                {activity.hasGpx && (
                  <div className="flex items-center gap-2 text-sm text-gray-500 py-1">
                    <span>📍</span>
                    <span>GPX добавлен</span>
                  </div>
                )}
                <button className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors py-1">
                  <span>✏️</span>
                  <span>Редактировать</span>
                </button>
                <button className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors py-1">
                  <span>🗑</span>
                  <span>Удалить</span>
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Bottom Action Bar - hidden when popup is open */}
      {!showParticipants && renderBottomBar()}

      {/* Participants Popup */}
      {showParticipants && (
        <ParticipantsPopup 
          participants={sampleParticipants.slice(0, activity.participants)}
          total={activity.participants}
          max={activity.maxParticipants}
          onClose={() => setShowParticipants(false)}
          actionButton={getActionButton()}
        />
      )}
    </div>
  );
};

// Demo Component with activity type switcher
export default function AydaRunActivityDetail() {
  const [activityType, setActivityType] = useState('club'); // 'club' | 'user' | 'private' | 'awaiting'
  const [isOrganizer, setIsOrganizer] = useState(false);

  const getActivity = () => {
    switch (activityType) {
      case 'user': return sampleActivityUser;
      case 'private': return sampleActivityPrivate;
      case 'awaiting': return sampleActivityAwaiting;
      default: return sampleActivity;
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Demo Controls */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 max-w-md mx-auto">
        <p className="text-xs text-gray-400 mb-2">Тип активности:</p>
        <div className="flex flex-wrap gap-2 mb-3">
          <button
            onClick={() => setActivityType('club')}
            className={`text-xs px-3 py-1.5 rounded-lg transition-colors ${
              activityType === 'club' ? 'bg-gray-800 text-white' : 'bg-gray-100 text-gray-600'
            }`}
          >
            Клуб/Группа
          </button>
          <button
            onClick={() => setActivityType('user')}
            className={`text-xs px-3 py-1.5 rounded-lg transition-colors ${
              activityType === 'user' ? 'bg-gray-800 text-white' : 'bg-gray-100 text-gray-600'
            }`}
          >
            Пользователь
          </button>
          <button
            onClick={() => setActivityType('private')}
            className={`text-xs px-3 py-1.5 rounded-lg transition-colors ${
              activityType === 'private' ? 'bg-gray-800 text-white' : 'bg-gray-100 text-gray-600'
            }`}
          >
            Закрытая
          </button>
          <button
            onClick={() => setActivityType('awaiting')}
            className={`text-xs px-3 py-1.5 rounded-lg transition-colors ${
              activityType === 'awaiting' ? 'bg-orange-400 text-white' : 'bg-orange-100 text-orange-600'
            }`}
          >
            Ждёт подтверждения
          </button>
        </div>
        <label className="flex items-center gap-2 text-sm text-gray-500">
          <input 
            type="checkbox" 
            checked={isOrganizer}
            onChange={(e) => setIsOrganizer(e.target.checked)}
            className="rounded"
          />
          Вид организатора
        </label>
      </div>

      {/* Activity Detail */}
      <ActivityDetail 
        key={activityType}
        activity={getActivity()}
        isOrganizer={isOrganizer}
      />
    </div>
  );
}
