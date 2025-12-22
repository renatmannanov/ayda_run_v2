import React, { useState } from 'react';

// Sample data - activities only on Saturday
const weekDays = [
  { id: 1, name: 'Сегодня, пн', shortName: 'Пн', date: '23 дек', activities: [] },
  { id: 2, name: 'Вт', shortName: 'Вт', date: '24 дек', activities: [] },
  { id: 3, name: 'Ср', shortName: 'Ср', date: '25 дек', activities: [] },
  { id: 4, name: 'Чт', shortName: 'Чт', date: '26 дек', activities: [] },
  { id: 5, name: 'Пт', shortName: 'Пт', date: '27 дек', activities: [] },
  { 
    id: 6, 
    name: 'Сб', 
    shortName: 'Сб', 
    date: '28 дек', 
    activities: [
      {
        id: 1,
        title: "Длинная в горы",
        organizer: { type: 'club', club: "SRG Almaty", group: "Горные бегуны" },
        time: "07:00",
        location: "Медеу",
        distance: "10 км",
        elevation: "850 м",
        sportIcon: "⛰️",
        participants: 8,
        maxParticipants: 20,
        status: 'registered',
        isPrivate: false
      },
      {
        id: 2,
        title: "Утренний бег",
        organizer: { type: 'club', club: "SRG Almaty", group: "Утренние бегуны" },
        time: "08:00",
        location: "Парк Первого Президента",
        distance: "5 км",
        elevation: null,
        sportIcon: "🏃",
        participants: 12,
        maxParticipants: 20,
        status: 'none',
        isPrivate: false
      }
    ] 
  },
  { id: 7, name: 'Вс', shortName: 'Вс', date: '29 дек', activities: [] },
];

// Status Button Component
const StatusButton = ({ status, isPrivate, onClick }) => {
  if (status === 'attended') {
    return (
      <div className="w-9 h-9 rounded-full border-[2.5px] border-green-500 flex items-center justify-center">
        <svg className="w-5 h-5 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      </div>
    );
  }
  
  if (status === 'registered') {
    return (
      <div className="w-9 h-9 rounded-full border-[2.5px] border-gray-400 flex items-center justify-center">
        <svg className="w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={3}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
        </svg>
      </div>
    );
  }
  
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

// Compact Activity Card
const ActivityCard = ({ activity }) => {
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
    <div className="bg-white border border-gray-200 rounded-xl p-4 mb-3 cursor-pointer hover:border-gray-300 transition-colors">
      <div className="flex items-start justify-between mb-1">
        <h3 className="text-base text-gray-800 font-medium">{activity.title}</h3>
        <span className="text-xl ml-2">{activity.sportIcon}</span>
      </div>
      
      <p className="text-sm text-gray-500 mb-1">{getOrganizerText()}</p>
      
      <p className="text-sm text-gray-500 mb-1">
        {activity.time} · {activity.location}
      </p>
      
      {getDistanceText() && (
        <p className="text-sm text-gray-500 mb-2">{getDistanceText()}</p>
      )}
      
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

// Day Row Component - Compact version
const DayRow = ({ day, isExpanded, onToggle }) => {
  const hasActivities = day.activities.length > 0;
  const isToday = day.name.includes('Сегодня');
  
  return (
    <div className="border-b border-gray-100">
      {/* Day Header - Always visible */}
      <button 
        onClick={onToggle}
        className="w-full flex items-center py-3 px-4 hover:bg-gray-50 transition-colors relative"
      >
        {/* Day name - left */}
        <span className={`text-sm font-medium ${isToday ? 'text-gray-800' : 'text-gray-600'} flex-shrink-0`}>
          {day.name}
        </span>
        
        {/* Left line */}
        <div className="flex-1 border-b border-gray-200 mx-2" />
        
        {/* "нет активностей" - absolutely centered */}
        {!hasActivities && (
          <span className="absolute left-1/2 -translate-x-1/2 text-xs text-gray-400 bg-white px-2">
            нет активностей
          </span>
        )}
        
        {/* Right line */}
        <div className="flex-1 border-b border-gray-200 mx-2" />
        
        {/* Count - right */}
        <span className={`text-sm flex-shrink-0 ${hasActivities ? 'text-gray-800 font-medium' : 'text-gray-400'}`}>
          {day.activities.length}
        </span>
      </button>
      
      {/* Activities - Show when has activities */}
      {hasActivities && (
        <div className="px-4 pb-3">
          {day.activities.map(activity => (
            <ActivityCard key={activity.id} activity={activity} />
          ))}
        </div>
      )}
    </div>
  );
};

// Main Home Component
export default function AydaRunHome() {
  const [filter, setFilter] = useState('my'); // 'my' | 'all'
  const [weekOffset, setWeekOffset] = useState(0); // 0 = current week, -1 = prev, +1 = next
  const [touchStart, setTouchStart] = useState(null);
  const [touchEnd, setTouchEnd] = useState(null);
  
  const totalActivities = weekDays.reduce((sum, day) => sum + day.activities.length, 0);

  // Swipe handlers
  const minSwipeDistance = 50;
  
  const onTouchStart = (e) => {
    setTouchEnd(null);
    setTouchStart(e.targetTouches[0].clientX);
  };
  
  const onTouchMove = (e) => {
    setTouchEnd(e.targetTouches[0].clientX);
  };
  
  const onTouchEnd = () => {
    if (!touchStart || !touchEnd) return;
    const distance = touchStart - touchEnd;
    const isLeftSwipe = distance > minSwipeDistance;
    const isRightSwipe = distance < -minSwipeDistance;
    
    if (isLeftSwipe) {
      setWeekOffset(prev => prev + 1); // Next week
    }
    if (isRightSwipe) {
      setWeekOffset(prev => prev - 1); // Prev week
    }
  };

  const getWeekLabel = () => {
    if (weekOffset === 0) return 'Текущая неделя';
    if (weekOffset === 1) return 'Следующая неделя';
    if (weekOffset === -1) return 'Прошлая неделя';
    if (weekOffset > 1) return `Через ${weekOffset} нед.`;
    return `${Math.abs(weekOffset)} нед. назад`;
  };

  const getWeekDates = () => {
    // Simplified for demo - would calculate real dates based on offset
    if (weekOffset === 0) return '22 дек. - 28 дек.';
    if (weekOffset === 1) return '29 дек. - 4 янв.';
    if (weekOffset === -1) return '15 дек. - 21 дек.';
    return '...';
  };

  return (
    <div className="min-h-screen bg-white flex flex-col max-w-md mx-auto">
      {/* Header */}
      <div className="border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <button 
              onClick={() => setFilter('my')}
              className={`text-sm ${filter === 'my' ? 'text-gray-800 font-medium' : 'text-gray-400'}`}
            >
              Мои
            </button>
            <span className="text-sm text-gray-300">/</span>
            <button 
              onClick={() => setFilter('all')}
              className={`text-sm ${filter === 'all' ? 'text-gray-800 font-medium' : 'text-gray-400'}`}
            >
              Все
            </button>
          </div>
          <span className="text-sm text-gray-400">{totalActivities}</span>
        </div>
      </div>

      {/* Days List - with swipe */}
      <div 
        className="flex-1 overflow-auto"
        onTouchStart={onTouchStart}
        onTouchMove={onTouchMove}
        onTouchEnd={onTouchEnd}
      >
        {weekDays.map(day => (
          <DayRow 
            key={day.id} 
            day={day}
          />
        ))}
      </div>

      {/* Week Navigation - Bottom Bar Style */}
      <div className="bg-white border-t border-gray-200 px-4 py-3">
        <div 
          className="flex items-center justify-between bg-gray-100 rounded-xl px-4 py-3 cursor-pointer select-none"
          onTouchStart={onTouchStart}
          onTouchMove={onTouchMove}
          onTouchEnd={onTouchEnd}
        >
          {/* Left buttons: << and < */}
          <div className="flex flex-col items-center gap-1 -ml-1">
            <button 
              onClick={() => setWeekOffset(prev => prev - 1)}
              className="text-gray-400 hover:text-gray-600 p-1"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19l-7-7 7-7" />
              </svg>
            </button>
            <button 
              onClick={() => setWeekOffset(0)}
              className={`p-1 transition-colors ${weekOffset > 0 ? 'text-gray-400 hover:text-gray-600' : 'text-gray-200'}`}
              disabled={weekOffset <= 0}
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M11 19l-7-7 7-7M18 19l-7-7 7-7" />
              </svg>
            </button>
          </div>
          
          <div className="text-center flex-1">
            <p className="text-sm font-medium text-gray-800">{getWeekLabel()}</p>
            <p className="text-xs text-gray-400">{getWeekDates()}</p>
          </div>
          
          {/* Right buttons: > and >> */}
          <div className="flex flex-col items-center gap-1 -mr-1">
            <button 
              onClick={() => setWeekOffset(prev => prev + 1)}
              className="text-gray-400 hover:text-gray-600 p-1"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
              </svg>
            </button>
            <button 
              onClick={() => setWeekOffset(0)}
              className={`p-1 transition-colors ${weekOffset < 0 ? 'text-gray-400 hover:text-gray-600' : 'text-gray-200'}`}
              disabled={weekOffset >= 0}
            >
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M13 5l7 7-7 7M6 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        </div>
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
