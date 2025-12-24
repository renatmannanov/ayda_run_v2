import React, { useState } from 'react';

// Sport types
const sportTypes = {
  run: { icon: '🏃', name: 'Бег' },
  trail: { icon: '⛰️', name: 'Трейл' },
  hike: { icon: '🥾', name: 'Хайкинг' },
  bike: { icon: '🚴', name: 'Вело' },
  yoga: { icon: '🧘', name: 'Йога' },
  workout: { icon: '💪', name: 'Воркаут' },
  swim: { icon: '🏊', name: 'Плавание' },
};

// Sample club data with links
const sampleClub = {
  id: 1,
  type: 'club',
  name: "SRG Almaty",
  description: "Тренируемся вместе с 2019 года. Все уровни подготовки — от новичков до ультрамарафонцев. Дружная атмосфера и регулярные тренировки.",
  icon: "🏆",
  members: 80,
  isMember: false,
  isAdmin: false,
  telegramRegistered: false,
  visibility: 'public', // 'public' | 'private'
  access: 'open', // 'open' | 'request'
  sports: ['run', 'trail', 'hike'], // виды спорта клуба
  links: [
    { id: 1, type: 'telegram', label: 'Общий чат', url: 'https://t.me/srg_almaty' },
    { id: 2, type: 'strava', label: 'Strava клуб', url: 'https://strava.com/clubs/srg' },
    { id: 3, type: 'instagram', label: 'Instagram', url: 'https://instagram.com/srg_almaty' }
  ],
  groups: [
    { id: 101, name: "Утренние бегуны", members: 15, telegramRegistered: true },
    { id: 102, name: "Горные бегуны", members: 12, telegramRegistered: false },
    { id: 103, name: "Выходные длинные", members: 30, telegramRegistered: true }
  ],
  activities: [
    { id: 1, title: "Утренняя пробежка", date: "Пн, 7:00", location: "Центральный парк", icon: "🏃" },
    { id: 2, title: "Интервалы", date: "Ср, 19:00", location: "Стадион", icon: "🏃" },
    { id: 3, title: "Длинная в горы", date: "Сб, 7:00", location: "Медеу", icon: "⛰️" }
  ],
  totalActivities: 24,
  participants: [
    { id: 1, name: "Анна", avatar: "👩", isAdmin: true },
    { id: 2, name: "Марат", avatar: "👨", isAdmin: true },
    { id: 3, name: "Дима", avatar: "👦", isAdmin: false },
    { id: 4, name: "Алия", avatar: "👩", isAdmin: false },
    { id: 5, name: "Саша", avatar: "👨", isAdmin: false },
    { id: 6, name: "Женя", avatar: "👩", isAdmin: false },
    { id: 7, name: "Костя", avatar: "👨", isAdmin: false },
    { id: 8, name: "Лена", avatar: "👩", isAdmin: false },
  ]
};

// Sample group data with links
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
  telegramRegistered: false,
  telegramChat: null,
  visibility: 'club', // 'public' | 'club'
  visibilityClubName: 'SRG Almaty',
  access: 'open', // 'open' | 'request'
  sports: ['trail', 'hike'], // виды спорта группы
  links: [
    { id: 1, type: 'telegram', label: 'Чат группы', url: 'https://t.me/srg_trail' },
    { id: 2, type: 'excel', label: 'Расписание', url: 'https://docs.google.com/spreadsheets/...' },
    { id: 3, type: 'strava', label: 'Strava сегмент', url: 'https://strava.com/segments/...' }
  ],
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

// Link type icons
const linkIcons = {
  telegram: '📱',
  strava: '🏃',
  instagram: '📷',
  excel: '📊',
  youtube: '🎬',
  website: '🌐',
  other: '🔗'
};

export default function AydaRunClubGroupDetailV2() {
  const [viewType, setViewType] = useState('club'); // 'club' | 'group'
  const [data, setData] = useState(sampleClub);
  const [showParticipants, setShowParticipants] = useState(false);
  const [showCreateMenu, setShowCreateMenu] = useState(false);
  const [showTelegramRegister, setShowTelegramRegister] = useState(false);
  const [showInviteMembers, setShowInviteMembers] = useState(false);
  const [showAddLink, setShowAddLink] = useState(false);

  // Update data when viewType changes
  React.useEffect(() => {
    setData(viewType === 'club' ? sampleClub : sampleGroup);
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

  // Displayed participants
  const displayedParticipants = data.participants?.slice(0, 5) || [];
  const remainingCount = (data.participants?.length || 0) - 5;

  // Link item component
  const LinkItem = ({ link }) => (
    <a 
      href={link.url}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-3 py-2 hover:bg-gray-50 rounded-lg px-2 -mx-2 transition-colors"
    >
      <span className="text-lg">{linkIcons[link.type] || linkIcons.other}</span>
      <span className="text-sm text-gray-700 flex-1">{link.label}</span>
      <span className="text-gray-400 text-sm">→</span>
    </a>
  );

  // Telegram Registration Sheet
  const TelegramRegisterSheet = () => (
    <div 
      className="fixed inset-0 bg-black/30 z-50 flex items-end justify-center"
      onClick={() => setShowTelegramRegister(false)}
    >
      <div 
        className="bg-white w-full max-w-md rounded-t-2xl p-6"
        onClick={e => e.stopPropagation()}
      >
        <h3 className="text-base font-medium text-gray-800 mb-2">Зарегистрировать через Telegram</h3>
        <p className="text-sm text-gray-500 mb-4">
          Подключи бота к Telegram группе, чтобы синхронизировать участников
        </p>

        {isClub && data.groups && data.groups.length > 0 ? (
          <>
            <p className="text-xs text-gray-400 mb-3">Выбери группы для регистрации:</p>
            <div className="space-y-2 mb-4">
              {data.groups.map(group => (
                <label 
                  key={group.id}
                  className={`flex items-center gap-3 p-3 border rounded-xl cursor-pointer transition-colors ${
                    group.telegramRegistered 
                      ? 'border-green-200 bg-green-50' 
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <input
                    type="checkbox"
                    defaultChecked={!group.telegramRegistered}
                    disabled={group.telegramRegistered}
                    className="w-4 h-4 rounded border-gray-300"
                  />
                  <div className="flex-1">
                    <p className="text-sm text-gray-800">{group.name}</p>
                    <p className="text-xs text-gray-500">{group.members} участников</p>
                  </div>
                  {group.telegramRegistered && (
                    <span className="text-xs text-green-600">✓ Подключено</span>
                  )}
                </label>
              ))}
            </div>
          </>
        ) : (
          <div className="bg-gray-50 rounded-xl p-4 mb-4">
            <p className="text-sm text-gray-700">
              После нажатия откроется инструкция по добавлению бота в вашу Telegram группу
            </p>
          </div>
        )}
        
        <button
          onClick={() => {
            setShowTelegramRegister(false);
            // Would navigate to telegram registration flow
          }}
          className="w-full py-3 bg-gray-800 text-white rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors mb-3"
        >
          {isClub ? 'Зарегистрировать выбранные' : 'Начать регистрацию'}
        </button>
        
        <button
          onClick={() => setShowTelegramRegister(false)}
          className="w-full py-3 text-gray-400 text-sm"
        >
          Отмена
        </button>
      </div>
    </div>
  );

  // Invite Members Sheet
  const InviteMembersSheet = () => (
    <div 
      className="fixed inset-0 bg-black/30 z-50 flex items-end justify-center"
      onClick={() => setShowInviteMembers(false)}
    >
      <div 
        className="bg-white w-full max-w-md rounded-t-2xl p-6"
        onClick={e => e.stopPropagation()}
      >
        <h3 className="text-base font-medium text-gray-800 mb-2">Пригласить участников</h3>
        <p className="text-sm text-gray-500 mb-4">
          Бот отправит приглашение в Telegram группу
        </p>

        {!data.telegramRegistered ? (
          <div className="bg-amber-50 border border-amber-100 rounded-xl p-4 mb-4">
            <p className="text-sm text-amber-800">
              ⚠️ Сначала зарегистрируй группу через Telegram
            </p>
          </div>
        ) : (
          <div className="bg-gray-50 rounded-xl p-4 mb-4">
            <p className="text-sm text-gray-700 mb-2">Бот отправит сообщение:</p>
            <div className="bg-white border border-gray-200 rounded-lg p-3">
              <p className="text-xs text-gray-600">
                Привет! 👋 Присоединяйся к <strong>{data.name}</strong> в Ayda Run — записывайся на тренировки в один клик!
              </p>
              <p className="text-xs text-blue-500 mt-2">[Открыть Ayda Run]</p>
            </div>
          </div>
        )}
        
        <button
          disabled={!data.telegramRegistered}
          className={`w-full py-3 rounded-xl text-sm font-medium mb-3 transition-colors ${
            data.telegramRegistered
              ? 'bg-gray-800 text-white hover:bg-gray-700'
              : 'bg-gray-100 text-gray-400 cursor-not-allowed'
          }`}
        >
          Отправить приглашение
        </button>
        
        <button
          onClick={() => setShowInviteMembers(false)}
          className="w-full py-3 text-gray-400 text-sm"
        >
          Отмена
        </button>
      </div>
    </div>
  );

  // Add Link Sheet
  const AddLinkSheet = () => (
    <div 
      className="fixed inset-0 bg-black/30 z-50 flex items-end justify-center"
      onClick={() => setShowAddLink(false)}
    >
      <div 
        className="bg-white w-full max-w-md rounded-t-2xl p-6"
        onClick={e => e.stopPropagation()}
      >
        <h3 className="text-base font-medium text-gray-800 mb-4">Добавить ссылку</h3>
        
        <div className="mb-4">
          <label className="text-sm text-gray-700 mb-2 block">Тип</label>
          <div className="flex flex-wrap gap-2">
            {Object.entries(linkIcons).map(([type, icon]) => (
              <button
                key={type}
                className="px-3 py-2 border border-gray-200 rounded-lg text-sm hover:border-gray-300 transition-colors"
              >
                {icon} {type}
              </button>
            ))}
          </div>
        </div>
        
        <div className="mb-4">
          <label className="text-sm text-gray-700 mb-2 block">Название</label>
          <input
            type="text"
            placeholder="Strava клуб"
            className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm outline-none focus:border-gray-400"
          />
        </div>
        
        <div className="mb-4">
          <label className="text-sm text-gray-700 mb-2 block">URL</label>
          <input
            type="url"
            placeholder="https://..."
            className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm outline-none focus:border-gray-400"
          />
        </div>
        
        <button className="w-full py-3 bg-gray-800 text-white rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors mb-3">
          Добавить
        </button>
        
        <button
          onClick={() => setShowAddLink(false)}
          className="w-full py-3 text-gray-400 text-sm"
        >
          Отмена
        </button>
      </div>
    </div>
  );

  // Participants Sheet
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
          <span className="text-base font-medium text-gray-800">Участники · {data.members}</span>
          <button onClick={() => setShowParticipants(false)} className="text-gray-400 text-xl">✕</button>
        </div>
        <div className="flex-1 overflow-auto px-4 py-2 pb-6">
          {data.participants?.map(p => (
            <div key={p.id} className="flex items-center justify-between py-3">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{p.avatar}</span>
                <span className="text-sm text-gray-700">{p.name}</span>
              </div>
              {p.isAdmin && <span className="text-xs text-gray-400">{isClub ? 'админ' : 'тренер'}</span>}
            </div>
          ))}
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
        <button className="w-full text-left py-3 flex items-center gap-3 hover:bg-gray-50 rounded-lg px-2">
          <span className="text-xl">🏃</span>
          <div>
            <span className="text-gray-700">Тренировку</span>
            <p className="text-xs text-gray-400">в {data.name}</p>
          </div>
        </button>
        {isClub && (
          <button className="w-full text-left py-3 flex items-center gap-3 hover:bg-gray-50 rounded-lg px-2">
            <span className="text-xl">👥</span>
            <div>
              <span className="text-gray-700">Группу</span>
              <p className="text-xs text-gray-400">в {data.name}</p>
            </div>
          </button>
        )}
        <button onClick={() => setShowCreateMenu(false)} className="w-full mt-4 py-3 text-gray-400 text-sm">
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
      <div className="flex items-center gap-2">
        <p className="text-sm text-gray-800 font-medium">{group.name}</p>
        {group.telegramRegistered && <span className="text-green-500 text-xs">✓</span>}
      </div>
      <p className="text-xs text-gray-500">{group.members} чел</p>
    </button>
  );

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col max-w-md mx-auto">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3">
        <div className="flex items-center justify-between">
          <button className="text-gray-500 text-sm hover:text-gray-700">← Назад</button>
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
          </div>
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
                <div className="flex items-start justify-between">
                  <h1 className="text-lg text-gray-800 font-medium">
                    {data.name}
                    {hasParentClub && <span className="text-gray-400 font-normal"> / {data.parentClub}</span>}
                  </h1>
                  {data.telegramRegistered && (
                    <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded">TG</span>
                  )}
                </div>
                <p className="text-sm text-gray-500 mt-1">
                  {data.members} участников
                  {isClub && data.groups?.length > 0 && ` · ${data.groups.length} групп`}
                  {' · '}
                  {isClub ? (
                    data.visibility === 'public' 
                      ? '🌐 Публичный' 
                      : '🔒 Закрытый'
                  ) : (
                    data.visibility === 'public'
                      ? '🌐 Публичная'
                      : `🏆 ${data.visibilityClubName || data.parentClub}`
                  )}
                </p>
                {/* Sports */}
                {data.sports && data.sports.length > 0 && (
                  <div className="flex gap-1 mt-2">
                    {data.sports.map(sportId => (
                      <span 
                        key={sportId} 
                        className="text-base"
                        title={sportTypes[sportId]?.name}
                      >
                        {sportTypes[sportId]?.icon}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className="border-t border-gray-300 my-4" />

          {/* Description */}
          <p className="text-sm text-gray-700 leading-relaxed">{data.description}</p>

          <div className="border-t border-gray-300 my-4" />

          {/* Activities - FIRST (most important) */}
          <div>
            <p className="text-sm text-gray-500 mb-3">Ближайшие тренировки</p>
            {data.activities.slice(0, 3).map(activity => (
              <MiniActivityCard key={activity.id} activity={activity} />
            ))}
            {data.totalActivities > 3 && (
              <button className="text-sm text-gray-500 hover:text-gray-700 mt-2">
                → Все ({data.totalActivities})
              </button>
            )}
          </div>

          <div className="border-t border-gray-300 my-4" />

          {/* Groups (for clubs) */}
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
              <div className="border-t border-gray-300 my-4" />
            </>
          )}

          {/* Participants (for both clubs and groups) */}
          <div className="mb-4">
            <p className="text-sm text-gray-500 mb-3">Участники ({data.members})</p>
            <button onClick={() => setShowParticipants(true)} className="flex items-center gap-1">
              <div className="flex -space-x-2">
                {displayedParticipants.map(p => (
                  <span key={p.id} className="text-2xl">{p.avatar}</span>
                ))}
              </div>
              {remainingCount > 0 && (
                <span className="text-sm text-gray-400 ml-2">+{remainingCount} →</span>
              )}
            </button>
          </div>

          {/* Links */}
          {data.links && data.links.length > 0 && (
            <>
              <div className="border-t border-gray-300 my-4" />
              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="text-sm text-gray-500">Ссылки</p>
                  {data.isAdmin && (
                    <button 
                      onClick={() => setShowAddLink(true)}
                      className="text-xs text-gray-400 hover:text-gray-600"
                    >
                      + Добавить
                    </button>
                  )}
                </div>
                {data.links.map(link => (
                  <LinkItem key={link.id} link={link} />
                ))}
              </div>
            </>
          )}

          {/* Admin actions */}
          {data.isAdmin && (
            <>
              <div className="border-t border-gray-200 mt-4 pt-4">
                <div className="flex flex-wrap gap-3 mb-4">
                  <button className="text-sm text-gray-500 hover:text-gray-700">⚙️ Настройки</button>
                  <button className="text-sm text-gray-500 hover:text-gray-700">✏️ Редактировать</button>
                </div>
                
                {/* Telegram integration */}
                <div className="space-y-2">
                  <button
                    onClick={() => setShowTelegramRegister(true)}
                    className="w-full py-3 border border-gray-200 rounded-xl text-sm text-gray-700 hover:bg-gray-50 transition-colors flex items-center justify-center gap-2"
                  >
                    <span>📱</span>
                    {data.telegramRegistered ? 'Управление Telegram' : 'Зарегистрировать через ТГ'}
                  </button>
                  
                  <button
                    onClick={() => setShowInviteMembers(true)}
                    className="w-full py-3 border border-gray-200 rounded-xl text-sm text-gray-700 hover:bg-gray-50 transition-colors flex items-center justify-center gap-2"
                  >
                    <span>👥</span>
                    Пригласить участников через ТГ
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
            <button onClick={toggleMembership} className="flex-1 py-4 bg-green-50 text-green-600 rounded-xl text-sm font-medium">
              Участник ✓
            </button>
            {data.isAdmin && (
              <button onClick={() => setShowCreateMenu(true)} className="w-14 h-14 bg-gray-800 text-white rounded-xl flex items-center justify-center text-xl hover:bg-gray-700">
                ＋
              </button>
            )}
          </>
        ) : (
          <button onClick={toggleMembership} className="flex-1 py-4 bg-gray-800 text-white rounded-xl text-sm font-medium hover:bg-gray-700">
            {data.access === 'request' ? (
              <>🔒 Подать заявку</>
            ) : (
              isClub ? 'Вступить в клуб' : 'Вступить в группу'
            )}
          </button>
        )}
      </div>

      {/* Sheets */}
      {showParticipants && <ParticipantsSheet />}
      {showCreateMenu && <CreateMenu />}
      {showTelegramRegister && <TelegramRegisterSheet />}
      {showInviteMembers && <InviteMembersSheet />}
      {showAddLink && <AddLinkSheet />}
    </div>
  );
}
