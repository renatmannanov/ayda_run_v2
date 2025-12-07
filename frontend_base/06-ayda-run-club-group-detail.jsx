import React, { useState } from 'react';

// Sample club data
const sampleClub = {
  id: 1,
  type: 'club',
  name: "SRG Almaty",
  description: "Тренируемся вместе с 2019 года. Все уровни подготовки — от новичков до ультрамарафонцев. Дружная атмосфера и регулярные тренировки.",
  icon: "🏆",
  members: 80,
  isMember: false,
  isAdmin: false,
  groups: [
    { id: 101, name: "Утренние бегуны", members: 15 },
    { id: 102, name: "Горные бегуны", members: 12 },
    { id: 103, name: "Выходные длинные", members: 30 }
  ],
  activities: [
    { id: 1, title: "Утренняя пробежка", date: "Пн, 7:00", location: "Центральный парк", icon: "🏃" },
    { id: 2, title: "Интервалы", date: "Ср, 19:00", location: "Стадион", icon: "🏃" },
    { id: 3, title: "Длинная в горы", date: "Сб, 7:00", location: "Медеу", icon: "⛰️" }
  ],
  totalActivities: 24,
  participants: [
    { id: 1, name: "Анна", avatar: "👩", isAdmin: true },
    { id: 2, name: "Марат", avatar: "👨", isAdmin: false },
    { id: 3, name: "Дима", avatar: "👦", isAdmin: false },
    { id: 4, name: "Алия", avatar: "👩", isAdmin: false },
    { id: 5, name: "Саша", avatar: "👨", isAdmin: false },
    { id: 6, name: "Женя", avatar: "👩", isAdmin: false },
    { id: 7, name: "Костя", avatar: "👨", isAdmin: false },
    { id: 8, name: "Лена", avatar: "👩", isAdmin: false },
  ]
};

// Sample group data
const sampleGroup = {
  id: 101,
  type: 'group',
  name: "Горные бегуны",
  parentClub: "SRG Almaty",
  parentClubId: 1,
  description: "Трейлы каждые выходные. Медеу, Шымбулак, Бутаковка, Кок-Жайляу. Средний и продвинутый уровень.",
  icon: "👥",
  members: 15,
  isMember: false,
  isAdmin: false,
  activities: [
    { id: 3, title: "Длинная в горы", date: "Сб, 7:00", location: "Медеу", icon: "⛰️" },
    { id: 4, title: "Трейл на Кок-Жайляу", date: "Вс, 6:00", location: "Кок-Жайляу", icon: "⛰️" }
  ],
  totalActivities: 12,
  participants: [
    { id: 1, name: "Анна", avatar: "👩", isAdmin: true },
    { id: 2, name: "Марат", avatar: "👨", isAdmin: false },
    { id: 3, name: "Дима", avatar: "👦", isAdmin: false },
    { id: 4, name: "Алия", avatar: "👩", isAdmin: false },
    { id: 5, name: "Саша", avatar: "👨", isAdmin: false },
  ]
};

// Sample independent group
const sampleIndependentGroup = {
  id: 104,
  type: 'group',
  name: "Горные велосипедисты",
  parentClub: null,
  parentClubId: null,
  description: "Катаем по горам на MTB. Выезды по выходным, разные маршруты каждую неделю.",
  icon: "👥",
  members: 8,
  isMember: true,
  isAdmin: true,
  activities: [
    { id: 5, title: "Велозаезд в горы", date: "Сб, 8:00", location: "Медеу", icon: "🚴" }
  ],
  totalActivities: 6,
  participants: [
    { id: 1, name: "Вы", avatar: "😊", isAdmin: true },
    { id: 2, name: "Артём", avatar: "👨", isAdmin: false },
    { id: 3, name: "Мира", avatar: "👩", isAdmin: false },
  ]
};

export default function AydaRunClubGroupDetail() {
  // Demo: switch between club, group, independent group
  const [viewType, setViewType] = useState('club'); // 'club' | 'group' | 'independent'
  
  const getData = () => {
    switch(viewType) {
      case 'club': return sampleClub;
      case 'group': return sampleGroup;
      case 'independent': return sampleIndependentGroup;
      default: return sampleClub;
    }
  };

  const [data, setData] = useState(getData());
  const [showParticipants, setShowParticipants] = useState(false);
  const [showCreateMenu, setShowCreateMenu] = useState(false);

  // Update data when viewType changes
  React.useEffect(() => {
    setData(getData());
  }, [viewType]);

  // Toggle membership
  const toggleMembership = () => {
    setData(prev => ({
      ...prev,
      isMember: !prev.isMember,
      members: prev.isMember ? prev.members - 1 : prev.members + 1
    }));
  };

  const isClub = data.type === 'club';
  const hasParentClub = data.type === 'group' && data.parentClub;

  // Displayed participants (first 5)
  const displayedParticipants = data.participants.slice(0, 5);
  const remainingCount = data.participants.length - 5;

  // Participants Bottom Sheet
  const ParticipantsSheet = () => (
    <div 
      className="fixed inset-0 bg-black/30 z-50 flex items-end justify-center"
      onClick={() => setShowParticipants(false)}
    >
      <div 
        className="bg-white w-full max-w-md rounded-t-2xl max-h-[60vh] flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        <div className="flex items-center justify-between px-4 py-4 border-b border-gray-200">
          <span className="text-base font-medium text-gray-800">
            Участники · {data.members}
          </span>
          <button
            onClick={() => setShowParticipants(false)}
            className="text-gray-400 hover:text-gray-600 text-xl"
          >
            ✕
          </button>
        </div>
        
        <div className="flex-1 overflow-auto px-4 py-2 pb-6">
          {data.participants.map(participant => (
            <div 
              key={participant.id}
              className="flex items-center justify-between py-3"
            >
              <div className="flex items-center gap-3">
                <span className="text-2xl">{participant.avatar}</span>
                <span className="text-sm text-gray-700">{participant.name}</span>
              </div>
              {participant.isAdmin && (
                <span className="text-xs text-gray-400">
                  {isClub ? 'админ' : 'тренер'}
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
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
          <div>
            <span className="text-gray-700">Тренировку</span>
            <p className="text-xs text-gray-400">в {data.name}</p>
          </div>
        </button>
        
        {isClub && (
          <button className="w-full text-left py-3 flex items-center gap-3 hover:bg-gray-50 rounded-lg px-2 transition-colors">
            <span className="text-xl">👥</span>
            <div>
              <span className="text-gray-700">Группу</span>
              <p className="text-xs text-gray-400">в {data.name}</p>
            </div>
          </button>
        )}
        
        <button
          onClick={() => setShowCreateMenu(false)}
          className="w-full mt-4 py-3 text-gray-400 text-sm hover:text-gray-600 transition-colors"
        >
          Отмена
        </button>
      </div>
    </div>
  );

  // Mini Activity Card
  const MiniActivityCard = ({ activity }) => (
    <div className="bg-white border border-gray-200 rounded-xl p-3 mb-2">
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <h4 className="text-sm text-gray-800 font-medium truncate">{activity.title}</h4>
          <p className="text-xs text-gray-500 mt-1">{activity.date} · {activity.location}</p>
        </div>
        <span className="text-lg ml-2">{activity.icon}</span>
      </div>
    </div>
  );

  // Group Chip
  const GroupChip = ({ group }) => (
    <button className="bg-gray-50 border border-gray-200 rounded-lg px-3 py-2 text-left hover:bg-gray-100 transition-colors">
      <p className="text-sm text-gray-800 font-medium">{group.name}</p>
      <p className="text-xs text-gray-500">{group.members} чел</p>
    </button>
  );

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col max-w-md mx-auto">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-4 flex items-center justify-between">
        <button className="text-gray-500 text-sm hover:text-gray-700">
          ← Назад
        </button>
        
        {/* Demo controls */}
        <div className="flex gap-1">
          <button
            onClick={() => setViewType('club')}
            className={`text-xs px-2 py-1 rounded ${viewType === 'club' ? 'bg-gray-800 text-white' : 'bg-gray-100 text-gray-500'}`}
          >
            Клуб
          </button>
          <button
            onClick={() => setViewType('group')}
            className={`text-xs px-2 py-1 rounded ${viewType === 'group' ? 'bg-gray-800 text-white' : 'bg-gray-100 text-gray-500'}`}
          >
            Группа
          </button>
          <button
            onClick={() => setViewType('independent')}
            className={`text-xs px-2 py-1 rounded ${viewType === 'independent' ? 'bg-gray-800 text-white' : 'bg-gray-100 text-gray-500'}`}
          >
            Незав.
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto px-4 py-4">
        <div className="border border-gray-200 rounded-xl p-4 bg-white">
          {/* Header */}
          <div className="mb-4">
            <div className="flex items-start gap-3">
              <span className="text-2xl">{data.icon}</span>
              <div className="flex-1">
                <h1 className="text-lg text-gray-800 font-medium">
                  {data.name}
                  {hasParentClub && (
                    <span className="text-gray-400 font-normal"> / {data.parentClub}</span>
                  )}
                  {hasParentClub && (
                    <span className="text-gray-400 font-normal text-sm"> →</span>
                  )}
                </h1>
                <p className="text-sm text-gray-500 mt-1">
                  {isClub 
                    ? `${data.members} участников · ${data.groups?.length || 0} ${data.groups?.length === 1 ? 'группа' : data.groups?.length < 5 ? 'группы' : 'групп'}`
                    : `${data.members} участников`
                  }
                </p>
              </div>
            </div>
          </div>

          {/* Divider */}
          <div className="border-t border-gray-300 my-4" />

          {/* Description */}
          <p className="text-sm text-gray-700 leading-relaxed">
            {data.description}
          </p>

          {/* Divider */}
          <div className="border-t border-gray-300 my-4" />

          {/* Groups (only for clubs) */}
          {isClub && data.groups && data.groups.length > 0 && (
            <>
              <div className="mb-4">
                <p className="text-sm text-gray-500 mb-3">Группы ({data.groups.length})</p>
                <div className="flex flex-wrap gap-2">
                  {data.groups.map(group => (
                    <GroupChip key={group.id} group={group} />
                  ))}
                </div>
              </div>

              {/* Divider */}
              <div className="border-t border-gray-300 my-4" />
            </>
          )}

          {/* Participants (only for groups) */}
          {!isClub && (
            <>
              <div className="mb-4">
                <p className="text-sm text-gray-500 mb-3">Участники</p>
                <button
                  onClick={() => setShowParticipants(true)}
                  className="flex items-center gap-1"
                >
                  <div className="flex -space-x-2">
                    {displayedParticipants.map(p => (
                      <span key={p.id} className="text-2xl">{p.avatar}</span>
                    ))}
                  </div>
                  {remainingCount > 0 && (
                    <span className="text-sm text-gray-400 ml-2">
                      +{remainingCount} →
                    </span>
                  )}
                </button>
              </div>

              {/* Divider */}
              <div className="border-t border-gray-300 my-4" />
            </>
          )}

          {/* Activities */}
          <div>
            <p className="text-sm text-gray-500 mb-3">Ближайшие</p>
            {data.activities.slice(0, 2).map(activity => (
              <MiniActivityCard key={activity.id} activity={activity} />
            ))}
            {data.totalActivities > 2 && (
              <button className="text-sm text-gray-500 hover:text-gray-700 transition-colors mt-2">
                → Все ({data.totalActivities})
              </button>
            )}
          </div>

          {/* Admin actions */}
          {data.isAdmin && (
            <>
              <div className="border-t border-gray-200 mt-4 pt-4">
                <div className="flex gap-4">
                  <button className="text-sm text-gray-500 hover:text-gray-700 transition-colors">
                    ⚙️ Настройки
                  </button>
                  <button className="text-sm text-gray-500 hover:text-gray-700 transition-colors">
                    ✏️ Редактировать
                  </button>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Bottom CTA */}
      <div className="px-4 pb-6 pt-2 flex gap-3">
        {data.isMember ? (
          <>
            <button
              onClick={toggleMembership}
              className="flex-1 py-4 bg-green-50 text-green-600 rounded-xl text-sm font-medium"
            >
              Участник ✓
            </button>
            {data.isAdmin && (
              <button
                onClick={() => setShowCreateMenu(true)}
                className="w-14 h-14 bg-gray-800 text-white rounded-xl flex items-center justify-center text-xl hover:bg-gray-700 transition-colors"
              >
                ＋
              </button>
            )}
          </>
        ) : (
          <button
            onClick={toggleMembership}
            className="flex-1 py-4 bg-gray-800 text-white rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors"
          >
            {isClub ? 'Вступить в клуб' : 'Вступить в группу'}
          </button>
        )}
      </div>

      {/* Participants sheet */}
      {showParticipants && <ParticipantsSheet />}
      
      {/* Create menu */}
      {showCreateMenu && <CreateMenu />}
    </div>
  );
}
