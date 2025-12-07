import React, { useState } from 'react';

// Sample user data
const sampleUser = {
  id: 123456789,
  name: "Ренат",
  username: "@renat_run",
  avatar: "😊",
  clubs: [
    { id: 1, name: "SRG Almaty", icon: "🏆", members: 80 },
    { id: 2, name: "Trail Nomads", icon: "🏆", members: 35 }
  ],
  groups: [
    { id: 101, name: "Утренние бегуны", parentClub: "SRG", icon: "👥", members: 15 },
    { id: 102, name: "Горные бегуны", parentClub: "SRG", icon: "👥", members: 12 },
    { id: 104, name: "Горные велосипедисты", parentClub: null, icon: "👥", members: 8 }
  ],
  stats: {
    totalActivities: 47,
    attended: 42,
    missed: 5,
    attendanceRate: 89
  },
  upcomingCount: 3
};

export default function AydaRunProfile() {
  const [user] = useState(sampleUser);
  const [showStats, setShowStats] = useState(false);
  const [showCreateMenu, setShowCreateMenu] = useState(false);

  // Mini Club Card
  const MiniClubCard = ({ club }) => (
    <button className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-left hover:bg-gray-100 transition-colors min-w-[120px]">
      <div className="flex items-center gap-2 mb-1">
        <span>{club.icon}</span>
        <span className="text-sm text-gray-800 font-medium truncate">{club.name}</span>
      </div>
      <p className="text-xs text-gray-500">{club.members} чел</p>
    </button>
  );

  // Mini Group Card
  const MiniGroupCard = ({ group }) => (
    <button className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-left hover:bg-gray-100 transition-colors min-w-[120px]">
      <div className="flex items-center gap-2 mb-1">
        <span>{group.icon}</span>
        <span className="text-sm text-gray-800 font-medium truncate">
          {group.name}
          {group.parentClub && <span className="text-gray-400 font-normal"> / {group.parentClub}</span>}
        </span>
      </div>
      <p className="text-xs text-gray-500">{group.members} чел</p>
    </button>
  );

  // Stats Modal (placeholder for future)
  const StatsModal = () => (
    <div 
      className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center px-4"
      onClick={() => setShowStats(false)}
    >
      <div 
        className="bg-white w-full max-w-sm rounded-2xl p-6"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-base font-medium text-gray-800">Статистика</h3>
          <button
            onClick={() => setShowStats(false)}
            className="text-gray-400 hover:text-gray-600 text-xl"
          >
            ✕
          </button>
        </div>

        <div className="space-y-4">
          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <span className="text-sm text-gray-600">Всего тренировок</span>
            <span className="text-sm font-medium text-gray-800">{user.stats.totalActivities}</span>
          </div>
          
          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <span className="text-sm text-gray-600">Посещено</span>
            <span className="text-sm font-medium text-green-600">{user.stats.attended}</span>
          </div>
          
          <div className="flex justify-between items-center py-2 border-b border-gray-100">
            <span className="text-sm text-gray-600">Пропущено</span>
            <span className="text-sm font-medium text-gray-400">{user.stats.missed}</span>
          </div>
          
          <div className="flex justify-between items-center py-2">
            <span className="text-sm text-gray-600">Посещаемость</span>
            <span className="text-sm font-medium text-gray-800">{user.stats.attendanceRate}%</span>
          </div>
        </div>

        {/* Progress bar */}
        <div className="mt-6">
          <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
            <div 
              className="h-full bg-green-500 rounded-full transition-all"
              style={{ width: `${user.stats.attendanceRate}%` }}
            />
          </div>
          <p className="text-xs text-gray-400 mt-2 text-center">
            {user.stats.attended} из {user.stats.totalActivities} тренировок
          </p>
        </div>
      </div>
    </div>
  );

  // Create Menu
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

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col max-w-md mx-auto">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3">
        <h1 className="text-base font-medium text-gray-800">Профиль</h1>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto px-4 py-4">
        {/* User Info Card */}
        <div className="border border-gray-200 rounded-xl p-6 bg-white mb-4">
          <div className="flex flex-col items-center text-center">
            <span className="text-5xl mb-3">{user.avatar}</span>
            <h2 className="text-lg text-gray-800 font-medium">{user.name}</h2>
            <p className="text-sm text-gray-500">{user.username}</p>
          </div>
        </div>

        {/* Clubs Section */}
        <div className="border border-gray-200 rounded-xl p-4 bg-white mb-4">
          <p className="text-sm text-gray-500 mb-3">Мои клубы ({user.clubs.length})</p>
          <div className="flex gap-2 overflow-x-auto pb-1">
            {user.clubs.map(club => (
              <MiniClubCard key={club.id} club={club} />
            ))}
          </div>
        </div>

        {/* Groups Section */}
        <div className="border border-gray-200 rounded-xl p-4 bg-white mb-4">
          <p className="text-sm text-gray-500 mb-3">Мои группы ({user.groups.length})</p>
          <div className="flex gap-2 overflow-x-auto pb-1">
            {user.groups.map(group => (
              <MiniGroupCard key={group.id} group={group} />
            ))}
          </div>
        </div>

        {/* Stats & Settings */}
        <div className="border border-gray-200 rounded-xl bg-white overflow-hidden">
          <button 
            onClick={() => setShowStats(true)}
            className="w-full px-4 py-4 flex items-center gap-3 hover:bg-gray-50 transition-colors border-b border-gray-100"
          >
            <span className="text-lg">📊</span>
            <span className="text-sm text-gray-700 flex-1 text-left">Статистика</span>
            <span className="text-sm text-gray-400">{user.stats.attendanceRate}%</span>
            <span className="text-gray-300">→</span>
          </button>
          
          <button className="w-full px-4 py-4 flex items-center gap-3 hover:bg-gray-50 transition-colors border-b border-gray-100">
            <span className="text-lg">🔔</span>
            <span className="text-sm text-gray-700 flex-1 text-left">Уведомления</span>
            <span className="text-gray-300">→</span>
          </button>
          
          <button className="w-full px-4 py-4 flex items-center gap-3 hover:bg-gray-50 transition-colors border-b border-gray-100">
            <span className="text-lg">🎨</span>
            <span className="text-sm text-gray-700 flex-1 text-left">Виды спорта</span>
            <span className="text-sm text-gray-400">4 выбрано</span>
            <span className="text-gray-300">→</span>
          </button>
          
          <button className="w-full px-4 py-4 flex items-center gap-3 hover:bg-gray-50 transition-colors">
            <span className="text-lg">⚙️</span>
            <span className="text-sm text-gray-700 flex-1 text-left">Настройки</span>
            <span className="text-gray-300">→</span>
          </button>
        </div>

        {/* App info */}
        <div className="mt-6 text-center">
          <p className="text-xs text-gray-400">Ayda Run v1.0</p>
          <p className="text-xs text-gray-300 mt-1">Made with ❤️ in Almaty</p>
        </div>
      </div>

      {/* Bottom Navigation */}
      <div className="bg-white border-t border-gray-200 px-4 py-3 flex items-center justify-around">
        <button className="flex flex-col items-center gap-1 text-gray-400 hover:text-gray-600 transition-colors">
          <span className="text-lg">🏠</span>
          <span className="text-xs">Home</span>
        </button>
        
        <button className="flex flex-col items-center gap-1 text-gray-400 hover:text-gray-600 transition-colors">
          <span className="text-lg">👥</span>
          <span className="text-xs">Клубы</span>
        </button>
        
        <button className="flex flex-col items-center gap-1 text-gray-800">
          <span className="text-lg">👤</span>
          <span className="text-xs font-medium">Я</span>
        </button>
        
        <button 
          onClick={() => setShowCreateMenu(true)}
          className="w-10 h-10 bg-gray-800 text-white rounded-xl flex items-center justify-center text-xl hover:bg-gray-700 transition-colors"
        >
          ＋
        </button>
      </div>

      {/* Stats Modal */}
      {showStats && <StatsModal />}
      
      {/* Create Menu */}
      {showCreateMenu && <CreateMenu />}
    </div>
  );
}
