import React, { useState } from 'react';

// Sample data
const userData = {
  name: "Renat Mannanov",
  username: "@ray_mann",
  initials: "RM",
  photo: null, // или URL фото
  sports: ["🏃", "🚴"],
  strava: "strava.com/athletes/renat", // или null
  showPhoto: false,
};

const clubsAndGroups = [
  { id: 1, type: 'club', name: "SRG Almaty", shortName: "SRG", avatar: "🏆" },
  { id: 2, type: 'club', name: "Club Runners", shortName: "CR", avatar: null },
  { id: 3, type: 'group', name: "Горные бегуны", shortName: "ГБ", avatar: null },
  { id: 4, type: 'group', name: "Trail Nomads", shortName: "TN", avatar: null },
];

// Stats by period
const statsByPeriod = {
  month: {
    registered: 12,
    attended: 10,
    clubs: [
      { name: "SRG Almaty", avatar: "🏆", registered: 6, attended: 5 },
      { name: "Club Runners", initials: "CR", registered: 4, attended: 4 },
      { name: "Горные бегуны", initials: "ГБ", registered: 2, attended: 1 },
    ],
    sports: [
      { icon: "🏃", name: "Бег", count: 7 },
      { icon: "⛰️", name: "Трейл", count: 2 },
      { icon: "🚴", name: "Вело", count: 1 },
    ],
    people: [
      { name: "Анна", avatar: "👩", count: 6 },
      { name: "Марат", avatar: "👨", count: 4 },
      { name: "Дима", avatar: "👦", count: 3 },
    ],
  },
  quarter: {
    registered: 38,
    attended: 34,
    clubs: [
      { name: "SRG Almaty", avatar: "🏆", registered: 18, attended: 17 },
      { name: "Club Runners", initials: "CR", registered: 12, attended: 11 },
      { name: "Горные бегуны", initials: "ГБ", registered: 8, attended: 6 },
    ],
    sports: [
      { icon: "🏃", name: "Бег", count: 24 },
      { icon: "⛰️", name: "Трейл", count: 7 },
      { icon: "🚴", name: "Вело", count: 3 },
    ],
    people: [
      { name: "Анна", avatar: "👩", count: 18 },
      { name: "Марат", avatar: "👨", count: 12 },
      { name: "Дима", avatar: "👦", count: 9 },
      { name: "Алия", avatar: "👩", count: 6 },
    ],
  },
  year: {
    registered: 94,
    attended: 87,
    clubs: [
      { name: "SRG Almaty", avatar: "🏆", registered: 45, attended: 42 },
      { name: "Club Runners", initials: "CR", registered: 30, attended: 28 },
      { name: "Горные бегуны", initials: "ГБ", registered: 19, attended: 17 },
    ],
    sports: [
      { icon: "🏃", name: "Бег", count: 62 },
      { icon: "⛰️", name: "Трейл", count: 18 },
      { icon: "🚴", name: "Вело", count: 7 },
    ],
    people: [
      { name: "Анна", avatar: "👩", count: 24 },
      { name: "Марат", avatar: "👨", count: 18 },
      { name: "Дима", avatar: "👦", count: 12 },
      { name: "Алия", avatar: "👩", count: 8 },
    ],
  },
  all: {
    registered: 156,
    attended: 142,
    clubs: [
      { name: "SRG Almaty", avatar: "🏆", registered: 78, attended: 72 },
      { name: "Club Runners", initials: "CR", registered: 48, attended: 44 },
      { name: "Горные бегуны", initials: "ГБ", registered: 30, attended: 26 },
    ],
    sports: [
      { icon: "🏃", name: "Бег", count: 98 },
      { icon: "⛰️", name: "Трейл", count: 32 },
      { icon: "🚴", name: "Вело", count: 12 },
    ],
    people: [
      { name: "Анна", avatar: "👩", count: 42 },
      { name: "Марат", avatar: "👨", count: 31 },
      { name: "Дима", avatar: "👦", count: 24 },
      { name: "Алия", avatar: "👩", count: 18 },
      { name: "Саша", avatar: "👨", count: 12 },
    ],
  },
};

// Avatar Component
const Avatar = ({ avatar, initials, size = "md" }) => {
  const sizeClasses = {
    sm: "w-10 h-10 text-sm",
    md: "w-12 h-12 text-base",
    lg: "w-16 h-16 text-xl",
  };
  
  if (avatar) {
    return (
      <div className={`${sizeClasses[size]} rounded-full bg-gray-100 flex items-center justify-center text-2xl`}>
        {avatar}
      </div>
    );
  }
  
  return (
    <div className={`${sizeClasses[size]} rounded-full bg-indigo-500 text-white flex items-center justify-center font-medium`}>
      {initials}
    </div>
  );
};

// Strava Link Component
const StravaLink = ({ url }) => {
  if (url) {
    return (
      <a 
        href={`https://${url}`}
        target="_blank"
        rel="noopener noreferrer"
        className="flex items-center gap-2 text-sm text-gray-500 hover:text-orange-500 transition-colors"
      >
        <span className="w-5 h-5 rounded bg-orange-500 text-white text-xs font-bold flex items-center justify-center">S</span>
        <span className="truncate">{url}</span>
        <svg className="w-4 h-4 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
        </svg>
      </a>
    );
  }
  
  return (
    <button className="flex items-center gap-2 text-sm text-orange-500 hover:text-orange-600 transition-colors">
      <span className="w-5 h-5 rounded bg-orange-100 text-orange-500 text-xs font-bold flex items-center justify-center">S</span>
      <span>Добавить Strava</span>
      <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
      </svg>
    </button>
  );
};

// Progress Bar Component
const ProgressBar = ({ value, max, showPercent = true }) => {
  const percent = max > 0 ? Math.round((value / max) * 100) : 0;
  
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-2 bg-gray-100 rounded-full overflow-hidden">
        <div 
          className="h-full bg-gray-300 rounded-full transition-all duration-300"
          style={{ width: `${percent}%` }}
        />
      </div>
      {showPercent && (
        <span className="text-sm text-gray-400 w-12 text-right">{percent}%</span>
      )}
    </div>
  );
};

// Club/Group Mini Card
const ClubGroupCard = ({ item }) => {
  return (
    <button className="flex flex-col items-center gap-1 min-w-[64px]">
      <Avatar 
        avatar={item.avatar} 
        initials={item.shortName} 
        size="md"
      />
      <span className="text-xs text-gray-600 max-w-[64px] truncate">{item.name}</span>
    </button>
  );
};

// Period Tabs
const PeriodTabs = ({ selected, onChange }) => {
  const periods = [
    { id: 'month', label: 'Месяц' },
    { id: 'quarter', label: 'Квартал' },
    { id: 'year', label: 'Год' },
    { id: 'all', label: 'Всё время' },
  ];
  
  return (
    <div className="flex gap-1 p-1 bg-gray-100 rounded-lg">
      {periods.map(period => (
        <button
          key={period.id}
          onClick={() => onChange(period.id)}
          className={`flex-1 py-1.5 px-2 text-xs font-medium rounded-md transition-colors ${
            selected === period.id 
              ? 'bg-white text-gray-800 shadow-sm' 
              : 'text-gray-500 hover:text-gray-700'
          }`}
        >
          {period.label}
        </button>
      ))}
    </div>
  );
};

// Statistics Page (separate screen)
const StatisticsPage = ({ onBack }) => {
  const [period, setPeriod] = useState('month');
  const stats = statsByPeriod[period];
  const totalSports = stats.sports.reduce((sum, s) => sum + s.count, 0);
  
  return (
    <div className="min-h-screen bg-gray-50 max-w-md mx-auto">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3">
        <button onClick={onBack} className="text-gray-500 hover:text-gray-700">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 className="text-lg font-medium text-gray-800">Статистика</h1>
      </div>
      
      <div className="p-4 space-y-4">
        {/* Period Tabs */}
        <div className="bg-white rounded-2xl p-4">
          <PeriodTabs selected={period} onChange={setPeriod} />
        </div>
        
        {/* Registered / Attended */}
        <div className="bg-white rounded-2xl p-4">
          <h3 className="text-sm font-medium text-gray-800 mb-3">Записался / Участвовал</h3>
          <div className="flex items-baseline justify-between mb-2">
            <span className="text-2xl font-medium text-gray-800">
              {stats.attended} <span className="text-gray-300">/</span> {stats.registered}
            </span>
            <span className="text-sm text-gray-400">
              {Math.round((stats.attended / stats.registered) * 100)}%
            </span>
          </div>
          <ProgressBar value={stats.attended} max={stats.registered} showPercent={false} />
        </div>
        
        {/* By Clubs & Groups */}
        <div className="bg-white rounded-2xl p-4">
          <h3 className="text-sm font-medium text-gray-800 mb-3">По клубам и группам</h3>
          <div className="space-y-3">
            {stats.clubs.map((club, i) => (
              <div key={i} className="flex items-center gap-3">
                <Avatar avatar={club.avatar} initials={club.initials} size="sm" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-baseline justify-between mb-1">
                    <span className="text-sm text-gray-700 truncate">{club.name}</span>
                    <span className="text-xs text-gray-400 ml-2">
                      {club.attended}/{club.registered}
                    </span>
                  </div>
                  <ProgressBar value={club.attended} max={club.registered} showPercent={false} />
                </div>
              </div>
            ))}
          </div>
        </div>
        
        {/* By Sports */}
        <div className="bg-white rounded-2xl p-4">
          <h3 className="text-sm font-medium text-gray-800 mb-3">По видам спорта</h3>
          <div className="space-y-3">
            {stats.sports.map((sport, i) => (
              <div key={i}>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm text-gray-700">
                    {sport.icon} {sport.name}
                  </span>
                  <span className="text-xs text-gray-400">{sport.count}</span>
                </div>
                <ProgressBar value={sport.count} max={totalSports} showPercent={false} />
              </div>
            ))}
          </div>
        </div>
        
        {/* Training Partners */}
        <div className="bg-white rounded-2xl p-4">
          <h3 className="text-sm font-medium text-gray-800 mb-3">Часто тренируюсь с</h3>
          <div className="space-y-2">
            {stats.people.map((person, i) => (
              <div key={i} className="flex items-center justify-between py-1">
                <div className="flex items-center gap-2">
                  <span className="text-xl">{person.avatar}</span>
                  <span className="text-sm text-gray-700">{person.name}</span>
                </div>
                <span className="text-xs text-gray-400">{person.count} совместных</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

// Statistics Link for Profile (preview)
const StatisticsPreview = ({ onClick }) => {
  const stats = statsByPeriod.month;
  const percent = Math.round((stats.attended / stats.registered) * 100);
  
  return (
    <button 
      onClick={onClick}
      className="w-full bg-white rounded-2xl p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
    >
      <div className="flex items-center gap-3">
        <span className="text-xl">📊</span>
        <span className="text-sm font-medium text-gray-800">Статистика</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-sm text-gray-400">{percent}%</span>
        <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
        </svg>
      </div>
    </button>
  );
};

// Settings Page
const SettingsPage = ({ onBack, showPhoto, setShowPhoto, strava }) => {
  return (
    <div className="min-h-screen bg-gray-50 max-w-md mx-auto">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center gap-3">
        <button onClick={onBack} className="text-gray-500 hover:text-gray-700">
          <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h1 className="text-lg font-medium text-gray-800">Настройки</h1>
      </div>
      
      <div className="p-4 space-y-4">
        {/* Photo Toggle */}
        <div className="bg-white rounded-2xl p-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-800">Показывать фото</p>
              <p className="text-xs text-gray-400 mt-0.5">Вместо инициалов в аватарке</p>
            </div>
            <button
              onClick={() => setShowPhoto(!showPhoto)}
              className={`w-12 h-7 rounded-full transition-colors ${
                showPhoto ? 'bg-gray-800' : 'bg-gray-200'
              }`}
            >
              <div className={`w-5 h-5 rounded-full bg-white shadow-sm transition-transform mx-1 ${
                showPhoto ? 'translate-x-5' : 'translate-x-0'
              }`} />
            </button>
          </div>
        </div>
        
        {/* Strava */}
        <div className="bg-white rounded-2xl p-4">
          <h3 className="text-sm font-medium text-gray-800 mb-3">Strava</h3>
          {strava ? (
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded bg-orange-500 text-white text-xs font-bold flex items-center justify-center">S</span>
                <span className="text-sm text-gray-600">{strava}</span>
              </div>
              <button className="text-xs text-red-500 hover:text-red-600">
                Отвязать
              </button>
            </div>
          ) : (
            <button className="w-full py-3 bg-orange-500 text-white rounded-xl text-sm font-medium hover:bg-orange-600 transition-colors flex items-center justify-center gap-2">
              <span className="font-bold">S</span>
              <span>Подключить Strava</span>
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

// Main Profile Component
export default function AydaRunProfile() {
  const [currentPage, setCurrentPage] = useState('profile'); // 'profile' | 'settings' | 'statistics'
  const [showPhoto, setShowPhoto] = useState(userData.showPhoto);
  const [hasStrava, setHasStrava] = useState(!!userData.strava);
  
  if (currentPage === 'settings') {
    return (
      <SettingsPage 
        onBack={() => setCurrentPage('profile')}
        showPhoto={showPhoto}
        setShowPhoto={setShowPhoto}
        strava={hasStrava ? userData.strava : null}
      />
    );
  }
  
  if (currentPage === 'statistics') {
    return (
      <StatisticsPage onBack={() => setCurrentPage('profile')} />
    );
  }
  
  return (
    <div className="min-h-screen bg-gray-50 max-w-md mx-auto">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3">
        <h1 className="text-lg font-medium text-gray-800">Профиль</h1>
      </div>
      
      <div className="p-4 space-y-4">
        {/* Profile Header - bigger avatar */}
        <div className="bg-white rounded-2xl p-4">
          <div className="flex items-center gap-5">
            {/* Avatar - bigger */}
            <div className="flex-shrink-0">
              {showPhoto && userData.photo ? (
                <img 
                  src={userData.photo} 
                  alt={userData.name}
                  className="w-20 h-20 rounded-full object-cover"
                />
              ) : (
                <div className="w-20 h-20 rounded-full bg-indigo-500 text-white flex items-center justify-center text-2xl font-medium">
                  {userData.initials}
                </div>
              )}
            </div>
            
            {/* Info - moved right */}
            <div className="flex-1 min-w-0">
              <h2 className="text-lg font-medium text-gray-800">{userData.name}</h2>
              <p className="text-sm text-gray-400">{userData.username}</p>
              
              {/* Sports */}
              <div className="flex gap-1 mt-1.5">
                {userData.sports.map((sport, i) => (
                  <span key={i} className="text-lg">{sport}</span>
                ))}
              </div>
              
              {/* Strava */}
              <div className="mt-2">
                <StravaLink url={hasStrava ? userData.strava : null} />
              </div>
            </div>
          </div>
        </div>
        
        {/* Clubs & Groups */}
        <div className="bg-white rounded-2xl p-4">
          <h3 className="text-sm font-medium text-gray-800 mb-3">
            Клубы и группы ({clubsAndGroups.length})
          </h3>
          <div className="flex gap-4 overflow-x-auto pb-2 -mx-1 px-1">
            {clubsAndGroups.map(item => (
              <ClubGroupCard key={item.id} item={item} />
            ))}
          </div>
        </div>
        
        {/* Statistics Link */}
        <StatisticsPreview onClick={() => setCurrentPage('statistics')} />
        
        {/* Settings Link */}
        <button 
          onClick={() => setCurrentPage('settings')}
          className="w-full bg-white rounded-2xl p-4 flex items-center justify-between hover:bg-gray-50 transition-colors"
        >
          <div className="flex items-center gap-3">
            <span className="text-xl">⚙️</span>
            <span className="text-sm font-medium text-gray-800">Настройки</span>
          </div>
          <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>
      
      {/* Bottom Nav */}
      <div className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 px-4 py-3 flex items-center justify-around max-w-md mx-auto">
        <button className="flex flex-col items-center gap-1 text-gray-400">
          <span className="text-lg">🏠</span>
          <span className="text-xs">Home</span>
        </button>
        <button className="flex flex-col items-center gap-1 text-gray-400">
          <span className="text-lg">👥</span>
          <span className="text-xs">Клубы</span>
        </button>
        <button className="flex flex-col items-center gap-1 text-gray-800">
          <span className="text-lg">👤</span>
          <span className="text-xs font-medium">Я</span>
        </button>
        <button className="w-10 h-10 bg-gray-800 text-white rounded-xl flex items-center justify-center text-xl">
          +
        </button>
      </div>
      
      {/* Bottom padding for nav */}
      <div className="h-20" />
    </div>
  );
}
