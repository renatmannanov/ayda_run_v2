import React, { useState } from 'react';

// Sample data
const sampleActivities = [
  {
    id: 1,
    title: "Утренняя пробежка",
    type: "running",
    icon: "🏃",
    date: new Date(2024, 11, 9, 7, 0), // Monday
    dayOfWeek: 1,
    location: "Центральный парк",
    distance: 10,
    elevation: 120,
    duration: "~1 ч",
    participants: 12,
    maxParticipants: 20,
    isJoined: true,
    isPast: false,
    attended: null
  },
  {
    id: 2,
    title: "Интервалы на стадионе",
    type: "running",
    icon: "🏃",
    date: new Date(2024, 11, 11, 19, 0), // Wednesday
    dayOfWeek: 3,
    location: "Стадион Динамо",
    distance: 8,
    elevation: 50,
    duration: "~50 мин",
    participants: 8,
    maxParticipants: 15,
    isJoined: false,
    isPast: false,
    attended: null
  },
  {
    id: 3,
    title: "Длинная в горы",
    type: "trail",
    icon: "⛰️",
    date: new Date(2024, 11, 14, 7, 0), // Saturday
    dayOfWeek: 6,
    location: "Медеу",
    distance: 21,
    elevation: 800,
    duration: "~3 ч",
    participants: 5,
    maxParticipants: 12,
    isJoined: false,
    isPast: false,
    attended: null
  },
  {
    id: 4,
    title: "Велозаезд по городу",
    type: "cycling",
    icon: "🚴",
    date: new Date(2024, 11, 15, 9, 0), // Sunday
    dayOfWeek: 0,
    location: "Площадь Республики",
    distance: 40,
    elevation: 200,
    duration: "~2 ч",
    participants: 15,
    maxParticipants: 30,
    isJoined: true,
    isPast: false,
    attended: null
  },
  // Past activities
  {
    id: 5,
    title: "Субботняя длинная",
    type: "running",
    icon: "🏃",
    date: new Date(2024, 11, 7, 8, 0), // Past Saturday
    dayOfWeek: 6,
    location: "Парк Первого Президента",
    distance: 15,
    elevation: 100,
    duration: "~1.5 ч",
    participants: 18,
    maxParticipants: 25,
    isJoined: true,
    isPast: true,
    attended: true
  },
  {
    id: 6,
    title: "Трейл на Кок-Жайляу",
    type: "trail",
    icon: "⛰️",
    date: new Date(2024, 11, 1, 7, 0), // Past Sunday
    dayOfWeek: 0,
    location: "Кок-Жайляу",
    distance: 18,
    elevation: 600,
    duration: "~2.5 ч",
    participants: 10,
    maxParticipants: 15,
    isJoined: true,
    isPast: true,
    attended: false
  }
];

const dayNames = {
  0: 'Вс',
  1: 'Пн',
  2: 'Вт',
  3: 'Ср',
  4: 'Чт',
  5: 'Пт',
  6: 'Сб'
};

const fullDayNames = {
  0: 'Воскресенье',
  1: 'Понедельник',
  2: 'Вторник',
  3: 'Среда',
  4: 'Четверг',
  5: 'Пятница',
  6: 'Суббота'
};

export default function AydaRunHome() {
  const [mode, setMode] = useState('my'); // 'my' | 'all'
  const [activities, setActivities] = useState(sampleActivities);
  const [showPast, setShowPast] = useState(false);
  const [showCreateMenu, setShowCreateMenu] = useState(false);

  // Filter activities
  const getFilteredActivities = () => {
    const upcoming = activities.filter(a => !a.isPast);
    if (mode === 'my') {
      return upcoming.filter(a => a.isJoined);
    }
    return upcoming;
  };

  const getPastActivities = () => {
    const past = activities.filter(a => a.isPast);
    if (mode === 'my') {
      return past.filter(a => a.isJoined);
    }
    return past;
  };

  const filteredActivities = getFilteredActivities();
  const pastActivities = getPastActivities();

  // Group by day of week (Mon-Sun order)
  const groupByDay = (acts) => {
    const days = [1, 2, 3, 4, 5, 6, 0]; // Mon to Sun
    const grouped = {};
    
    days.forEach(day => {
      grouped[day] = acts.filter(a => a.dayOfWeek === day);
    });
    
    return grouped;
  };

  const groupedActivities = groupByDay(filteredActivities);

  // Toggle join
  const toggleJoin = (activityId) => {
    setActivities(activities.map(a => 
      a.id === activityId 
        ? { ...a, isJoined: !a.isJoined, participants: a.isJoined ? a.participants - 1 : a.participants + 1 }
        : a
    ));
  };

  // Format time
  const formatTime = (date) => {
    return date.toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
  };

  // Check if today
  const isToday = (dayOfWeek) => {
    return new Date().getDay() === dayOfWeek;
  };

  // Activity Card Component
  const ActivityCard = ({ activity }) => {
    const isFull = activity.participants >= activity.maxParticipants;
    
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-4 mb-3">
        <div className="flex justify-between items-start mb-2">
          <h3 className="text-base text-gray-800 font-medium pr-2">
            {activity.title}
          </h3>
          <span className="text-xl flex-shrink-0">{activity.icon}</span>
        </div>
        
        <p className="text-sm text-gray-500 mb-2">
          {formatTime(activity.date)} · {activity.location}
        </p>
        
        <p className="text-sm text-gray-400 mb-3">
          {activity.distance} км · ↗{activity.elevation} м · {activity.duration}
        </p>
        
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">
            {activity.participants}/{activity.maxParticipants}
          </span>
          
          {activity.isPast ? (
            <span className={`text-sm ${activity.attended ? 'text-gray-500' : 'text-gray-400'}`}>
              {activity.attended ? 'Был ✓' : 'Пропустил'}
            </span>
          ) : activity.isJoined ? (
            <button
              onClick={() => toggleJoin(activity.id)}
              className="text-sm text-green-600 font-medium"
            >
              Иду ✓
            </button>
          ) : isFull ? (
            <span className="text-sm text-gray-400">
              Мест нет
            </span>
          ) : (
            <button
              onClick={() => toggleJoin(activity.id)}
              className="text-sm text-gray-600 hover:text-gray-800 transition-colors"
            >
              Записаться
            </button>
          )}
        </div>
      </div>
    );
  };

  // Day Section Component
  const DaySection = ({ dayOfWeek, activities }) => {
    const today = isToday(dayOfWeek);
    const hasActivities = activities.length > 0;
    
    return (
      <div className="mb-4">
        <div className="flex items-center gap-2 mb-3">
          <span className={`text-sm font-medium ${today ? 'text-gray-800' : 'text-gray-500'}`}>
            {today ? `Сегодня, ${dayNames[dayOfWeek].toLowerCase()}` : dayNames[dayOfWeek]}
          </span>
          <div className="flex-1 border-b border-gray-200" />
        </div>
        
        {hasActivities ? (
          activities.map(activity => (
            <ActivityCard key={activity.id} activity={activity} />
          ))
        ) : (
          <p className="text-sm text-gray-300 mb-3 pl-1">нет тренировок</p>
        )}
      </div>
    );
  };

  // Toggle Component
  const Toggle = () => (
    <div className="flex items-center gap-1 text-sm">
      <button
        onClick={() => setMode('my')}
        className={`transition-colors ${
          mode === 'my' 
            ? 'text-gray-900 font-medium' 
            : 'text-gray-400 hover:text-gray-600'
        }`}
      >
        Мои
      </button>
      <span className="text-gray-300">/</span>
      <button
        onClick={() => setMode('all')}
        className={`transition-colors ${
          mode === 'all' 
            ? 'text-gray-900 font-medium' 
            : 'text-gray-400 hover:text-gray-600'
        }`}
      >
        Все
      </button>
    </div>
  );

  // Empty State
  const EmptyState = () => (
    <div className="flex-1 flex flex-col items-center justify-center text-center px-8 py-12">
      <span className="text-4xl mb-4">📅</span>
      <h2 className="text-base text-gray-700 mb-2">Пока пусто</h2>
      <p className="text-sm text-gray-400 mb-6">Запишись на тренировку</p>
      <button
        onClick={() => setMode('all')}
        className="text-sm text-gray-600 hover:text-gray-800 transition-colors"
      >
        Смотреть все →
      </button>
    </div>
  );

  // Create Menu (Bottom Sheet)
  const CreateMenu = () => (
    <div 
      className="fixed inset-0 bg-black/30 z-50 flex items-end justify-center"
      onClick={() => setShowCreateMenu(false)}
    >
      <div 
        className="bg-white w-full max-w-md rounded-t-2xl p-6"
        onClick={e => e.stopPropagation()}
      >
        <h3 className="text-base font-medium text-gray-800 mb-4">Создать</h3>
        
        <button className="w-full text-left py-3 flex items-center gap-3 hover:bg-gray-50 rounded-lg px-2 transition-colors">
          <span className="text-xl">🏃</span>
          <span className="text-gray-700">Тренировку</span>
        </button>
        
        <button className="w-full text-left py-3 flex items-center gap-3 hover:bg-gray-50 rounded-lg px-2 transition-colors">
          <span className="text-xl">🏆</span>
          <span className="text-gray-700">Клуб</span>
        </button>
        
        <button className="w-full text-left py-3 flex items-center gap-3 hover:bg-gray-50 rounded-lg px-2 transition-colors">
          <span className="text-xl">👥</span>
          <span className="text-gray-700">Группу</span>
        </button>
        
        <button
          onClick={() => setShowCreateMenu(false)}
          className="w-full mt-4 py-3 text-gray-400 text-sm hover:text-gray-600 transition-colors"
        >
          Отмена
        </button>
      </div>
    </div>
  );

  const upcomingCount = filteredActivities.length;
  const hasUpcoming = upcomingCount > 0;

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col max-w-md mx-auto">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between sticky top-0 z-10">
        <Toggle />
        <span className="text-sm text-gray-400">{upcomingCount}</span>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto px-4 py-4">
        {hasUpcoming ? (
          <>
            {/* Week days */}
            {[1, 2, 3, 4, 5, 6, 0].map(day => (
              <DaySection 
                key={day} 
                dayOfWeek={day} 
                activities={groupedActivities[day]} 
              />
            ))}
            
            {/* Past activities */}
            {pastActivities.length > 0 && (
              <div className="mt-6">
                <button
                  onClick={() => setShowPast(!showPast)}
                  className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 transition-colors mb-3"
                >
                  <span>Прошедшие ({pastActivities.length})</span>
                  <span className={`transition-transform ${showPast ? 'rotate-180' : ''}`}>
                    ▾
                  </span>
                </button>
                
                {showPast && (
                  <div className="space-y-3">
                    {pastActivities.map(activity => (
                      <ActivityCard key={activity.id} activity={activity} />
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        ) : (
          <EmptyState />
        )}
      </div>

      {/* Bottom Navigation */}
      <div className="bg-white border-t border-gray-200 px-4 py-3 flex items-center justify-around">
        <button className="flex flex-col items-center gap-1 text-gray-800">
          <span className="text-lg">🏠</span>
          <span className="text-xs font-medium">Home</span>
        </button>
        
        <button className="flex flex-col items-center gap-1 text-gray-400 hover:text-gray-600 transition-colors">
          <span className="text-lg">👥</span>
          <span className="text-xs">Клубы</span>
        </button>
        
        <button className="flex flex-col items-center gap-1 text-gray-400 hover:text-gray-600 transition-colors">
          <span className="text-lg">👤</span>
          <span className="text-xs">Я</span>
        </button>
        
        <button 
          onClick={() => setShowCreateMenu(true)}
          className="w-10 h-10 bg-gray-800 text-white rounded-xl flex items-center justify-center text-xl hover:bg-gray-700 transition-colors"
        >
          ＋
        </button>
      </div>

      {/* Create Menu */}
      {showCreateMenu && <CreateMenu />}
    </div>
  );
}
