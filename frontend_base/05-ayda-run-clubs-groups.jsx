import React, { useState } from 'react';

// Sample data
const sampleClubs = [
  {
    id: 1,
    type: 'club',
    name: "SRG Almaty",
    description: "Беговой клуб",
    members: 80,
    groups: 3,
    isMember: true,
    icon: "🏆"
  },
  {
    id: 2,
    type: 'club',
    name: "Bike Almaty",
    description: "Велоклуб",
    members: 45,
    groups: 2,
    isMember: false,
    icon: "🏆"
  },
  {
    id: 3,
    type: 'club',
    name: "Trail Nomads",
    description: "Трейлраннинг клуб",
    members: 35,
    groups: 1,
    isMember: false,
    icon: "🏆"
  }
];

const sampleGroups = [
  {
    id: 101,
    type: 'group',
    name: "Утренние бегуны",
    parentClub: "SRG Almaty",
    parentClubId: 1,
    members: 15,
    isMember: true,
    icon: "👥"
  },
  {
    id: 102,
    type: 'group',
    name: "Горные бегуны",
    parentClub: "SRG Almaty",
    parentClubId: 1,
    members: 12,
    isMember: true,
    icon: "👥"
  },
  {
    id: 103,
    type: 'group',
    name: "Выходные длинные",
    parentClub: "SRG Almaty",
    parentClubId: 1,
    members: 30,
    isMember: false,
    icon: "👥"
  },
  {
    id: 104,
    type: 'group',
    name: "Горные велосипедисты",
    parentClub: null, // Independent group
    parentClubId: null,
    members: 8,
    isMember: true,
    icon: "👥"
  },
  {
    id: 105,
    type: 'group',
    name: "Trail Runners",
    parentClub: "Trail Nomads",
    parentClubId: 3,
    members: 22,
    isMember: false,
    icon: "👥"
  }
];

export default function AydaRunClubsGroups() {
  const [clubs, setClubs] = useState(sampleClubs);
  const [groups, setGroups] = useState(sampleGroups);
  const [showCreateMenu, setShowCreateMenu] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [showSearch, setShowSearch] = useState(false);
  const [joinConfirm, setJoinConfirm] = useState(null); // { type: 'club'|'group', item: {...} }

  // Get my clubs and groups
  const myClubs = clubs.filter(c => c.isMember);
  const myGroups = groups.filter(g => g.isMember);

  // Get discover items (not member)
  const discoverClubs = clubs.filter(c => !c.isMember);
  const discoverGroups = groups.filter(g => !g.isMember);

  // Combine and filter by search
  const filterBySearch = (items) => {
    if (!searchQuery.trim()) return items;
    const query = searchQuery.toLowerCase();
    return items.filter(item => 
      item.name.toLowerCase().includes(query) ||
      (item.parentClub && item.parentClub.toLowerCase().includes(query))
    );
  };

  // Show join confirmation popup
  const showJoinConfirm = (type, item) => {
    setJoinConfirm({ type, item });
  };

  // Handle join confirmation
  const handleJoinConfirm = () => {
    if (!joinConfirm) return;
    
    if (joinConfirm.type === 'club') {
      // For clubs: send request (simulated)
      alert('Заявка отправлена! Ожидайте подтверждения.');
    } else {
      // For groups: redirect to Telegram (simulated)
      alert('Переход в Telegram...');
    }
    
    setJoinConfirm(null);
  };

  // Toggle membership (for leaving)
  const toggleClubMembership = (clubId) => {
    setClubs(clubs.map(c => 
      c.id === clubId ? { ...c, isMember: !c.isMember, members: c.isMember ? c.members - 1 : c.members + 1 } : c
    ));
  };

  const toggleGroupMembership = (groupId) => {
    setGroups(groups.map(g => 
      g.id === groupId ? { ...g, isMember: !g.isMember, members: g.isMember ? g.members - 1 : g.members + 1 } : g
    ));
  };

  // Club Card Component
  const ClubCard = ({ club, showJoinButton = false }) => (
    <div className="bg-white border border-gray-200 rounded-xl p-4 mb-3">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3 flex-1">
          <span className="text-xl">{club.icon}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="text-base text-gray-800 font-medium truncate">
                {club.name}
              </h3>
              {club.isMember && !showJoinButton && (
                <span className="text-green-600 text-sm">✓</span>
              )}
            </div>
            <p className="text-sm text-gray-500 mt-1">
              {club.members} участников · {club.groups} {club.groups === 1 ? 'группа' : club.groups < 5 ? 'группы' : 'групп'}
            </p>
          </div>
        </div>
        
        {showJoinButton && (
          <button
            onClick={() => showJoinConfirm('club', club)}
            className="text-sm text-gray-600 hover:text-gray-800 transition-colors ml-2"
          >
            Вступить
          </button>
        )}
      </div>
    </div>
  );

  // Group Card Component
  const GroupCard = ({ group, showJoinButton = false }) => (
    <div className="bg-white border border-gray-200 rounded-xl p-4 mb-3">
      <div className="flex items-start justify-between">
        <div className="flex items-start gap-3 flex-1">
          <span className="text-xl">{group.icon}</span>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="text-base text-gray-800 font-medium truncate">
                {group.name}
                {group.parentClub && (
                  <span className="text-gray-400 font-normal"> / {group.parentClub}</span>
                )}
              </h3>
              {group.isMember && !showJoinButton && (
                <span className="text-green-600 text-sm flex-shrink-0">✓</span>
              )}
            </div>
            <p className="text-sm text-gray-500 mt-1">
              {group.members} участников
            </p>
          </div>
        </div>
        
        {showJoinButton && (
          <button
            onClick={() => showJoinConfirm('group', group)}
            className="text-sm text-gray-600 hover:text-gray-800 transition-colors ml-2"
          >
            Вступить
          </button>
        )}
      </div>
    </div>
  );

  // Search Header
  const SearchHeader = () => (
    <div className="bg-white border-b border-gray-200 px-4 py-3">
      <div className="flex items-center gap-3">
        <button
          onClick={() => {
            setShowSearch(false);
            setSearchQuery('');
          }}
          className="text-gray-500 hover:text-gray-700"
        >
          ←
        </button>
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Поиск клубов и групп..."
          className="flex-1 text-sm text-gray-800 placeholder-gray-400 outline-none"
          autoFocus
        />
        {searchQuery && (
          <button
            onClick={() => setSearchQuery('')}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        )}
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

  // Join Confirmation Popup
  const JoinConfirmPopup = () => {
    if (!joinConfirm) return null;
    
    const isClub = joinConfirm.type === 'club';
    const itemName = joinConfirm.item.name;
    
    return (
      <div 
        className="fixed inset-0 bg-black/30 z-50 flex items-center justify-center px-4"
        onClick={() => setJoinConfirm(null)}
      >
        <div 
          className="bg-white w-full max-w-sm rounded-2xl p-6"
          onClick={e => e.stopPropagation()}
        >
          <div className="text-center mb-6">
            <span className="text-3xl mb-3 block">{isClub ? '🏆' : '👥'}</span>
            <h3 className="text-base font-medium text-gray-800 mb-2">
              {isClub ? 'Вступить в клуб?' : 'Вступить в группу?'}
            </h3>
            <p className="text-sm text-gray-500">
              {isClub 
                ? `Отправить заявку на вступление в ${itemName}?`
                : `Перенаправить вас в Telegram для вступления в ${itemName}?`
              }
            </p>
          </div>
          
          <div className="flex gap-3">
            <button
              onClick={() => setJoinConfirm(null)}
              className="flex-1 py-3 border border-gray-200 rounded-xl text-sm text-gray-600 hover:bg-gray-50 transition-colors"
            >
              Нет
            </button>
            <button
              onClick={handleJoinConfirm}
              className="flex-1 py-3 bg-gray-800 text-white rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors"
            >
              Да
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Search Results View
  if (showSearch) {
    const filteredClubs = filterBySearch([...clubs]);
    const filteredGroups = filterBySearch([...groups]);
    const hasResults = filteredClubs.length > 0 || filteredGroups.length > 0;

    return (
      <div className="min-h-screen bg-gray-50 flex flex-col max-w-md mx-auto">
        <SearchHeader />
        
        <div className="flex-1 overflow-auto px-4 py-4">
          {!searchQuery.trim() ? (
            <p className="text-sm text-gray-400 text-center py-8">
              Введите название клуба или группы
            </p>
          ) : !hasResults ? (
            <div className="text-center py-8">
              <span className="text-3xl mb-3 block">🔍</span>
              <p className="text-sm text-gray-500">Ничего не найдено</p>
            </div>
          ) : (
            <>
              {filteredClubs.length > 0 && (
                <div className="mb-6">
                  <p className="text-sm text-gray-500 mb-3">Клубы</p>
                  {filteredClubs.map(club => (
                    <ClubCard 
                      key={club.id} 
                      club={club} 
                      showJoinButton={!club.isMember}
                    />
                  ))}
                </div>
              )}
              
              {filteredGroups.length > 0 && (
                <div>
                  <p className="text-sm text-gray-500 mb-3">Группы</p>
                  {filteredGroups.map(group => (
                    <GroupCard 
                      key={group.id} 
                      group={group} 
                      showJoinButton={!group.isMember}
                    />
                  ))}
                </div>
              )}
            </>
          )}
        </div>

        {/* Bottom Navigation */}
        <div className="bg-white border-t border-gray-200 px-4 py-3 flex items-center justify-around">
          <button className="flex flex-col items-center gap-1 text-gray-400 hover:text-gray-600 transition-colors">
            <span className="text-lg">🏠</span>
            <span className="text-xs">Home</span>
          </button>
          
          <button className="flex flex-col items-center gap-1 text-gray-800">
            <span className="text-lg">👥</span>
            <span className="text-xs font-medium">Клубы</span>
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

        {showCreateMenu && <CreateMenu />}
        {joinConfirm && <JoinConfirmPopup />}
      </div>
    );
  }

  // Main View
  return (
    <div className="min-h-screen bg-gray-50 flex flex-col max-w-md mx-auto">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 flex items-center justify-between sticky top-0 z-10">
        <h1 className="text-base font-medium text-gray-800">Клубы и группы</h1>
        <button
          onClick={() => setShowSearch(true)}
          className="text-gray-400 hover:text-gray-600 text-lg"
        >
          🔍
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto px-4 py-4">
        {/* My clubs and groups */}
        {(myClubs.length > 0 || myGroups.length > 0) && (
          <div className="mb-6">
            <p className="text-sm text-gray-500 mb-3">Мои</p>
            
            {myClubs.map(club => (
              <ClubCard key={club.id} club={club} />
            ))}
            
            {myGroups.map(group => (
              <GroupCard key={group.id} group={group} />
            ))}
          </div>
        )}

        {/* Discover */}
        {(discoverClubs.length > 0 || discoverGroups.length > 0) && (
          <div>
            <p className="text-sm text-gray-500 mb-3">Найти ещё</p>
            
            {discoverClubs.map(club => (
              <ClubCard key={club.id} club={club} showJoinButton />
            ))}
            
            {discoverGroups.map(group => (
              <GroupCard key={group.id} group={group} showJoinButton />
            ))}
          </div>
        )}

        {/* Empty state */}
        {myClubs.length === 0 && myGroups.length === 0 && discoverClubs.length === 0 && discoverGroups.length === 0 && (
          <div className="text-center py-12">
            <span className="text-4xl mb-4 block">👥</span>
            <h2 className="text-base text-gray-700 mb-2">Пока нет клубов</h2>
            <p className="text-sm text-gray-400 mb-6">Создай свой или найди по ссылке</p>
            <button
              onClick={() => setShowCreateMenu(true)}
              className="text-sm text-gray-600 hover:text-gray-800 transition-colors"
            >
              Создать клуб →
            </button>
          </div>
        )}
      </div>

      {/* Bottom Navigation */}
      <div className="bg-white border-t border-gray-200 px-4 py-3 flex items-center justify-around">
        <button className="flex flex-col items-center gap-1 text-gray-400 hover:text-gray-600 transition-colors">
          <span className="text-lg">🏠</span>
          <span className="text-xs">Home</span>
        </button>
        
        <button className="flex flex-col items-center gap-1 text-gray-800">
          <span className="text-lg">👥</span>
          <span className="text-xs font-medium">Клубы</span>
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
      
      {/* Join Confirmation */}
      {joinConfirm && <JoinConfirmPopup />}
    </div>
  );
}
