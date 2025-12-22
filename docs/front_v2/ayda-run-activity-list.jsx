import React, { useState } from 'react';

// Sample data
const sampleActivities = [
  {
    id: 1,
    title: "Длинная в горы",
    organizer: { type: 'club', club: "SRG Almaty", group: "Горные бегуны" },
    date: "сб, 27 дек",
    time: "07:00",
    location: "Медеу",
    distance: "10 км",
    elevation: "850 м",
    sportIcon: "⛰️",
    participants: 8,
    maxParticipants: 20,
    status: 'registered',
    isPrivate: false,
    hasGpx: true
  },
  {
    id: 2,
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
    status: 'none',
    isPrivate: false,
    hasGpx: false
  },
  {
    id: 3,
    title: "Вечерний бег в парке",
    organizer: { type: 'user', name: "Марат", avatar: "👨" },
    date: "вт, 24 дек",
    time: "19:00",
    location: "Центральный парк",
    distance: "5 км",
    elevation: null,
    sportIcon: "🏃",
    participants: 3,
    maxParticipants: 10,
    status: 'none',
    isPrivate: false,
    hasGpx: false
  },
  {
    id: 4,
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
    hasGpx: true
  },
  {
    id: 5,
    title: "Интервалы на стадионе",
    organizer: { type: 'club', club: "SRG Almaty", group: "Утренние бегуны" },
    date: "ср, 25 дек",
    time: "07:00",
    location: "Стадион",
    distance: "8 км",
    elevation: null,
    sportIcon: "🏃",
    participants: 12,
    maxParticipants: 20,
    status: 'attended',
    isPrivate: false,
    hasGpx: false
  }
];

// Status Button Component - Improved Design
const StatusButton = ({ status, isPrivate, onClick }) => {
  // Attended - green outlined circle with green checkmark (not filled)
  if (status === 'attended') {
    return (
      <div className="w-9 h-9 rounded-full border-[2.5px] border-green-500 flex items-center justify-center">
        <svg className="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      </div>
    );
  }
  
  // Registered - gray circle with gray checkmark
  if (status === 'registered') {
    return (
      <div className="w-9 h-9 rounded-full border-[2.5px] border-gray-400 flex items-center justify-center">
        <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      </div>
    );
  }
  
  // Not registered - circle with plus (same style as checkmarks)
  return (
    <div className="flex items-center gap-1.5">
      {isPrivate && (
        <svg className="w-7 h-7 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      )}
      <button 
        onClick={onClick}
        className="w-9 h-9 rounded-full border-[2.5px] border-gray-400 flex items-center justify-center text-gray-400 hover:border-gray-500 hover:text-gray-500 transition-colors"
      >
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M12 6v12m6-6H6" />
        </svg>
      </button>
    </div>
  );
};

// Activity Card Component
const ActivityCard = ({ activity, onClick }) => {
  const getOrganizerText = () => {
    if (activity.organizer.type === 'user') {
      return (
        <span className="flex items-center gap-1">
          <span className="text-gray-400">организатор</span>
          <span>{activity.organizer.avatar}</span>
          <span>{activity.organizer.name}</span>
        </span>
      );
    }
    return `${activity.organizer.club} · ${activity.organizer.group}`;
  };

  const getDistanceText = () => {
    if (!activity.distance && !activity.elevation) return null;
    const parts = [];
    if (activity.distance) parts.push(activity.distance);
    if (activity.elevation) parts.push(`↗ ${activity.elevation}`);
    return parts.join(' · ');
  };

  return (
    <div 
      onClick={onClick}
      className="bg-white border border-gray-200 rounded-xl p-4 mb-3 cursor-pointer hover:border-gray-300 transition-colors"
    >
      {/* Title + Sport Icon */}
      <div className="flex items-start justify-between mb-1">
        <h3 className="text-base text-gray-800 font-medium">{activity.title}</h3>
        <span className="text-xl ml-2">{activity.sportIcon}</span>
      </div>
      
      {/* Organizer */}
      <p className="text-sm text-gray-500 mb-1">{getOrganizerText()}</p>
      
      {/* Date, Time, Location */}
      <p className="text-sm text-gray-500 mb-1">
        {activity.date} · {activity.time} · {activity.location}
      </p>
      
      {/* Distance & Elevation (if exists) */}
      {getDistanceText() && (
        <p className="text-sm text-gray-500 mb-2">{getDistanceText()}</p>
      )}
      
      {/* Participants + Status */}
      <div className="flex items-center justify-between mt-3">
        <span className="text-sm text-gray-500">
          {activity.participants}/{activity.maxParticipants}
        </span>
        <StatusButton 
          status={activity.status} 
          isPrivate={activity.isPrivate}
          onClick={(e) => e.stopPropagation()}
        />
      </div>
    </div>
  );
};

// Main Activity List Component
export default function AydaRunActivityList() {
  const [activities, setActivities] = useState(sampleActivities);

  const toggleStatus = (id) => {
    setActivities(prev => prev.map(a => {
      if (a.id === id) {
        const newStatus = a.status === 'none' ? 'registered' : 
                          a.status === 'registered' ? 'none' : a.status;
        return { ...a, status: newStatus };
      }
      return a;
    }));
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col max-w-md mx-auto">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-800 font-medium">Мои</span>
            <span className="text-sm text-gray-400">/</span>
            <span className="text-sm text-gray-500">Все</span>
          </div>
          <span className="text-sm text-gray-400">{activities.length}</span>
        </div>
      </div>

      {/* Week Header */}
      <div className="bg-white px-4 py-3 text-center border-b border-gray-200">
        <p className="text-sm font-medium text-gray-800">Текущая неделя</p>
        <p className="text-xs text-gray-400">22 дек. - 28 дек.</p>
      </div>

      {/* Activity List */}
      <div className="flex-1 overflow-auto px-4 py-4">
        {activities.map(activity => (
          <ActivityCard 
            key={activity.id}
            activity={activity}
            onClick={() => console.log('Navigate to activity', activity.id)}
          />
        ))}
      </div>

      {/* Bottom Nav */}
      <div className="bg-white border-t border-gray-200 px-4 py-3 flex items-center justify-around">
        <button className="flex flex-col items-center gap-1 text-gray-800">
          <span className="text-lg">🏠</span>
          <span className="text-xs font-medium">Home</span>
        </button>
        <button className="flex flex-col items-center gap-1 text-gray-400">
          <span className="text-lg">👥</span>
          <span className="text-xs">Клубы</span>
        </button>
        <button className="flex flex-col items-center gap-1 text-gray-400">
          <span className="text-lg">👤</span>
          <span className="text-xs">Я</span>
        </button>
        <button className="w-10 h-10 bg-gray-800 text-white rounded-xl flex items-center justify-center text-xl">
          +
        </button>
      </div>
    </div>
  );
}
