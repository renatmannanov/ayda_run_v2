import React, { useState } from 'react';

// Sample activity data
const sampleActivity = {
  id: 1,
  title: "Длинная в горы",
  type: "trail",
  icon: "⛰️",
  date: "Сб, 14 дек",
  time: "7:00",
  endTime: "~10:00",
  location: "Медеу, парковка у катка",
  distance: 21,
  elevation: 800,
  duration: "~3 часа",
  difficulty: "Сложная",
  description: "Бежим до Шымбулака и обратно. Обязательно вода, гель, ветровка. Трансфер не нужен.",
  gpxLink: "https://example.com/route.gpx",
  club: "SRG Almaty",
  group: "Горные бегуны",
  participants: [
    { id: 1, name: "Анна", avatar: "👩", isOrganizer: true, attended: true },
    { id: 2, name: "Марат", avatar: "👨", isOrganizer: false, attended: true },
    { id: 3, name: "Дима", avatar: "👦", isOrganizer: false, attended: false },
    { id: 4, name: "Алия", avatar: "👩", isOrganizer: false, attended: true },
    { id: 5, name: "Саша", avatar: "👨", isOrganizer: false, attended: true },
    { id: 6, name: "Женя", avatar: "👩", isOrganizer: false, attended: true },
    { id: 7, name: "Костя", avatar: "👨", isOrganizer: false, attended: true },
    { id: 8, name: "Лена", avatar: "👩", isOrganizer: false, attended: null },
    { id: 9, name: "Артём", avatar: "👦", isOrganizer: false, attended: null },
    { id: 10, name: "Мира", avatar: "👩", isOrganizer: false, attended: null },
    { id: 11, name: "Олег", avatar: "👨", isOrganizer: false, attended: null },
    { id: 12, name: "Катя", avatar: "👩", isOrganizer: false, attended: null },
  ],
  maxParticipants: 20,
  isJoined: false,
  isPast: false,
  userAttended: null // null = not marked, true = attended, false = missed
};

export default function AydaRunActivityDetail() {
  const [activity, setActivity] = useState(sampleActivity);
  const [showParticipants, setShowParticipants] = useState(false);
  const [isOrganizer, setIsOrganizer] = useState(false);
  const [isPast, setIsPast] = useState(false);
  const [isAttendanceMode, setIsAttendanceMode] = useState(false);
  const [attendanceData, setAttendanceData] = useState(
    activity.participants.map(p => ({ ...p, checked: true }))
  );

  // Toggle join
  const toggleJoin = () => {
    setActivity(prev => ({
      ...prev,
      isJoined: !prev.isJoined,
      participants: prev.isJoined 
        ? prev.participants.slice(0, -1)
        : [...prev.participants, { id: 99, name: "Вы", avatar: "😊", isOrganizer: false, attended: null }]
    }));
  };

  // Toggle attendance checkbox
  const toggleAttendance = (participantId) => {
    setAttendanceData(prev => 
      prev.map(p => p.id === participantId ? { ...p, checked: !p.checked } : p)
    );
  };

  // Select all attendance
  const selectAllAttendance = () => {
    const allChecked = attendanceData.every(p => p.checked);
    setAttendanceData(prev => prev.map(p => ({ ...p, checked: !allChecked })));
  };

  // Save attendance
  const saveAttendance = () => {
    setActivity(prev => ({
      ...prev,
      participants: prev.participants.map(p => {
        const data = attendanceData.find(a => a.id === p.id);
        return { ...p, attended: data ? data.checked : p.attended };
      })
    }));
    setIsAttendanceMode(false);
  };

  // Count attended
  const attendedCount = activity.participants.filter(p => p.attended === true).length;
  const totalRegistered = activity.participants.length;

  // Participants Bottom Sheet
  const ParticipantsSheet = () => (
    <div 
      className="fixed inset-0 bg-black/30 z-50 flex items-end justify-center"
      onClick={() => setShowParticipants(false)}
    >
      <div 
        className="bg-white w-full max-w-md rounded-t-2xl max-h-[60vh] flex flex-col mb-0"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-4 py-4 border-b border-gray-200">
          <span className="text-base font-medium text-gray-800">
            Участники · {isPast && activity.participants.some(p => p.attended !== null) 
              ? `${attendedCount}/${totalRegistered} были`
              : `${activity.participants.length}/${activity.maxParticipants}`
            }
          </span>
          <button
            onClick={() => setShowParticipants(false)}
            className="text-gray-400 hover:text-gray-600 text-xl"
          >
            ✕
          </button>
        </div>
        
        <div className="flex-1 overflow-auto px-4 py-2 pb-6">
          {activity.participants.map(participant => (
            <div 
              key={participant.id}
              className={`flex items-center justify-between py-3 ${
                isPast && participant.attended === false ? 'opacity-50' : ''
              }`}
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">{participant.avatar}</span>
                <span className={`text-sm ${
                  isPast && participant.attended === false 
                    ? 'text-gray-400 line-through' 
                    : 'text-gray-700'
                }`}>
                  {participant.name}
                </span>
              </div>
              <span className="text-xs text-gray-400">
                {participant.isOrganizer && 'организатор'}
                {isPast && participant.attended === true && '✓'}
                {isPast && participant.attended === false && '—'}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  // Attendance Mode Screen
  const AttendanceMode = () => {
    const allChecked = attendanceData.every(p => p.checked);
    
    return (
      <div className="min-h-screen bg-white flex flex-col max-w-md mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-4 border-b border-gray-200">
          <button
            onClick={() => setIsAttendanceMode(false)}
            className="text-gray-500 text-sm hover:text-gray-700"
          >
            ← Отмена
          </button>
          <button
            onClick={saveAttendance}
            className="text-green-600 text-sm font-medium hover:text-green-700"
          >
            Сохранить ✓
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-auto px-4 py-4">
          <h2 className="text-base font-medium text-gray-800 mb-4">
            Кто был на тренировке?
          </h2>
          
          {attendanceData.map(participant => (
            <button
              key={participant.id}
              onClick={() => toggleAttendance(participant.id)}
              className="w-full flex items-center gap-3 py-3 hover:bg-gray-50 rounded-lg transition-colors"
            >
              <div className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                participant.checked 
                  ? 'bg-gray-800 border-gray-800' 
                  : 'border-gray-300'
              }`}>
                {participant.checked && (
                  <svg className="w-3 h-3 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                  </svg>
                )}
              </div>
              <span className="text-2xl">{participant.avatar}</span>
              <span className="text-sm text-gray-700">{participant.name}</span>
            </button>
          ))}
          
          <div className="border-t border-gray-200 mt-4 pt-4">
            <button
              onClick={selectAllAttendance}
              className="text-sm text-gray-500 hover:text-gray-700 transition-colors"
            >
              {allChecked ? '☐ Снять все' : '✓ Выбрать всех'}
            </button>
          </div>
        </div>
      </div>
    );
  };

  // If in attendance mode, show that screen
  if (isAttendanceMode) {
    return <AttendanceMode />;
  }

  // Check if full
  const isFull = activity.participants.length >= activity.maxParticipants;

  // Get displayed participants (first 5)
  const displayedParticipants = activity.participants.slice(0, 5);
  const remainingCount = activity.participants.length - 5;

  return (
    <div className="min-h-screen bg-white flex flex-col max-w-md mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-4 border-b border-gray-200">
        <button className="text-gray-500 text-sm hover:text-gray-700">
          ← Назад
        </button>
        
        {/* Demo controls */}
        <div className="flex gap-2">
          <button
            onClick={() => setIsOrganizer(!isOrganizer)}
            className={`text-xs px-2 py-1 rounded ${isOrganizer ? 'bg-orange-100 text-orange-600' : 'bg-gray-100 text-gray-500'}`}
          >
            Орг
          </button>
          <button
            onClick={() => setIsPast(!isPast)}
            className={`text-xs px-2 py-1 rounded ${isPast ? 'bg-blue-100 text-blue-600' : 'bg-gray-100 text-gray-500'}`}
          >
            Прошло
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto px-4 py-4">
        <div className="border border-gray-200 rounded-xl p-4">
        {/* Title */}
        <div className="flex justify-between items-start mb-4">
          <div>
            <h1 className="text-xl text-gray-800 font-medium mb-1">
              {activity.title}
            </h1>
            {isPast && (
              <span className="text-sm text-gray-400">
                Прошла · {activity.date}
              </span>
            )}
          </div>
          <span className="text-3xl">{activity.icon}</span>
        </div>

        {/* Info */}
        <div className="space-y-3 mb-4">
          <div className="flex items-start gap-3">
            <span className="text-gray-400">📅</span>
            <span className="text-sm text-gray-700">
              {activity.date}, {activity.time} – {activity.endTime}
            </span>
          </div>
          
          <div className="flex items-start gap-3">
            <span className="text-gray-400">📍</span>
            <span className="text-sm text-gray-700">
              {activity.location}
            </span>
          </div>
          
          <div className="flex items-start gap-3">
            <span className="text-gray-400">🏃</span>
            <span className="text-sm text-gray-700">
              {activity.distance} км · ↗{activity.elevation} м · {activity.duration}
            </span>
          </div>
          
          <div className="flex items-start gap-3">
            <span className="text-gray-400">⚡</span>
            <span className="text-sm text-gray-700">
              {activity.difficulty}
            </span>
          </div>
          
          {activity.gpxLink && (
            <div className="flex items-start gap-3">
              <span className="text-gray-400">📎</span>
              <a 
                href={activity.gpxLink}
                className="text-sm text-gray-700 hover:text-gray-900 underline underline-offset-2"
              >
                Маршрут GPX →
              </a>
            </div>
          )}
        </div>

        {/* Divider */}
        <div className="border-t border-gray-300 my-4" />

        {/* Description */}
        <p className="text-sm text-gray-700 leading-relaxed mb-4">
          {activity.description}
        </p>

        {/* Divider */}
        <div className="border-t border-gray-300 my-4" />

        {/* Participants */}
        <div className="mb-4">
          <p className="text-sm text-gray-500 mb-3">
            Участники · {isPast && activity.participants.some(p => p.attended !== null)
              ? `${attendedCount} из ${totalRegistered} были`
              : `${activity.participants.length}/${activity.maxParticipants}`
            }
          </p>
          
          <button
            onClick={() => setShowParticipants(true)}
            className="flex items-center gap-1"
          >
            <div className="flex -space-x-2">
              {displayedParticipants.map(p => (
                <span 
                  key={p.id}
                  className={`text-2xl ${isPast && p.attended === false ? 'opacity-40' : ''}`}
                >
                  {p.avatar}
                </span>
              ))}
            </div>
            {remainingCount > 0 && (
              <span className="text-sm text-gray-400 ml-2">
                +{remainingCount} →
              </span>
            )}
          </button>
          
          {/* User attendance status (past activities) */}
          {isPast && activity.isJoined && (
            <p className={`text-sm mt-3 ${
              activity.userAttended ? 'text-green-600' : 'text-gray-400'
            }`}>
              {activity.userAttended ? 'Ты был ✓' : 'Ты пропустил'}
            </p>
          )}
        </div>

        {/* Club/Group */}
        <button className="text-sm text-gray-500 hover:text-gray-700 transition-colors">
          {activity.club} / {activity.group} →
        </button>

        {/* Organizer actions */}
        {isOrganizer && (
          <div className="mt-6 pt-4 border-t border-gray-200">
            <div className="flex gap-4 mb-4">
              <button className="text-sm text-gray-500 hover:text-gray-700 transition-colors">
                ✏️ Редактировать
              </button>
              <button className="text-sm text-gray-500 hover:text-gray-700 transition-colors">
                🔗 Поделиться
              </button>
            </div>
            
            {isPast && (
              <button
                onClick={() => setIsAttendanceMode(true)}
                className="w-full py-3 border border-gray-200 rounded-xl text-sm text-gray-700 hover:bg-gray-50 transition-colors"
              >
                Отметить посещаемость
              </button>
            )}
          </div>
        )}
        </div>
      </div>

      {/* Bottom CTA */}
      {!isPast && (
        <div className="px-4 pb-6 pt-2">
          {activity.isJoined ? (
            <button
              onClick={toggleJoin}
              className="w-full py-4 bg-green-50 text-green-600 rounded-xl text-sm font-medium flex items-center justify-center gap-2"
            >
              <span>Иду ✓</span>
              <span className="text-green-400">·</span>
              <span className="text-green-500 font-normal">Отменить</span>
            </button>
          ) : isFull ? (
            <button
              disabled
              className="w-full py-4 bg-gray-100 text-gray-400 rounded-xl text-sm font-medium cursor-not-allowed"
            >
              Мест нет
            </button>
          ) : (
            <button
              onClick={toggleJoin}
              className="w-full py-4 bg-gray-800 text-white rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors"
            >
              Записаться
            </button>
          )}
        </div>
      )}

      {/* Participants sheet */}
      {showParticipants && <ParticipantsSheet />}
    </div>
  );
}
