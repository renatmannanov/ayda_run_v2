import React, { useState } from 'react';

const sampleClubs = [
  { id: 1, name: 'SRG Almaty', icon: '🏆' },
  { id: 2, name: 'Trail Nomads', icon: '🏆' },
  { id: 3, name: 'Bike Almaty', icon: '🏆' }
];

export default function AydaRunCreateGroup() {
  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [selectedClub, setSelectedClub] = useState('');
  const [isIndependent, setIsIndependent] = useState(false);
  const [telegramChat, setTelegramChat] = useState('');
  const [joinAccess, setJoinAccess] = useState('club'); // 'club' | 'invite'
  const [errors, setErrors] = useState({});
  const [showClubPicker, setShowClubPicker] = useState(false);
  const [isCreated, setIsCreated] = useState(false);
  const [shareLink, setShareLink] = useState('');

  // Validation
  const validate = () => {
    const newErrors = {};
    if (!name.trim()) newErrors.name = true;
    if (!isIndependent && !selectedClub) newErrors.club = true;
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Submit
  const handleSubmit = () => {
    if (validate()) {
      setShareLink('https://t.me/aydarun_bot?start=group_xyz789');
      setIsCreated(true);
    }
  };

  // Toggle independent
  const toggleIndependent = () => {
    setIsIndependent(!isIndependent);
    if (!isIndependent) {
      setSelectedClub('');
    }
  };

  // Get selected club
  const getSelectedClubName = () => {
    const club = sampleClubs.find(c => c.id.toString() === selectedClub);
    return club ? club.name : 'Выбрать клуб...';
  };

  // Copy link
  const copyLink = () => {
    navigator.clipboard.writeText(shareLink);
    alert('Ссылка скопирована!');
  };

  // Success screen
  if (isCreated) {
    return (
      <div className="min-h-screen bg-white flex flex-col max-w-md mx-auto">
        <div className="flex-1 flex flex-col items-center justify-center px-6 text-center">
          <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mb-6">
            <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          
          <h1 className="text-xl text-gray-800 font-medium mb-2">
            Группа создана!
          </h1>
          <p className="text-sm text-gray-500 mb-8">
            Пригласи участников по ссылке
          </p>
          
          <div className="w-full bg-gray-50 border border-gray-200 rounded-xl p-4 mb-4">
            <p className="text-xs text-gray-400 mb-2">Ссылка для приглашения</p>
            <p className="text-sm text-gray-800 break-all">{shareLink}</p>
          </div>
          
          <div className="flex gap-3 w-full">
            <button
              onClick={copyLink}
              className="flex-1 py-3 border border-gray-200 rounded-xl text-sm text-gray-700 hover:bg-gray-50 transition-colors"
            >
              Копировать
            </button>
            <button
              className="flex-1 py-3 bg-gray-800 text-white rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors"
            >
              Поделиться
            </button>
          </div>
        </div>
        
        <div className="px-4 pb-6">
          <button className="w-full py-4 text-gray-500 text-sm hover:text-gray-700 transition-colors">
            Перейти в группу →
          </button>
        </div>
      </div>
    );
  }

  // Club picker popup
  const ClubPicker = () => (
    <div 
      className="fixed inset-0 bg-black/30 z-50 flex items-end justify-center"
      onClick={() => setShowClubPicker(false)}
    >
      <div 
        className="bg-white w-full max-w-md rounded-t-2xl p-6"
        onClick={e => e.stopPropagation()}
      >
        <h3 className="text-base font-medium text-gray-800 mb-4">Выбрать клуб</h3>
        
        {sampleClubs.map(club => (
          <button
            key={club.id}
            onClick={() => {
              setSelectedClub(club.id.toString());
              setShowClubPicker(false);
            }}
            className={`w-full text-left py-3 px-2 rounded-lg flex items-center gap-3 transition-colors ${
              selectedClub === club.id.toString() ? 'bg-gray-100' : 'hover:bg-gray-50'
            }`}
          >
            <span className="text-xl">{club.icon}</span>
            <span className="text-sm text-gray-700">{club.name}</span>
          </button>
        ))}
        
        <button
          onClick={() => setShowClubPicker(false)}
          className="w-full mt-4 py-3 text-gray-400 text-sm"
        >
          Отмена
        </button>
      </div>
    </div>
  );

  // Input component
  const Input = ({ label, value, onChange, placeholder, error, required, helper }) => (
    <div className="mb-4">
      <label className="text-sm text-gray-700 mb-2 block">
        {label} {required && <span className="text-red-400">*</span>}
      </label>
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className={`w-full px-4 py-3 border rounded-xl text-sm text-gray-800 placeholder-gray-400 outline-none transition-colors ${
          error ? 'border-red-300 bg-red-50' : 'border-gray-200 focus:border-gray-400'
        }`}
      />
      {helper && <p className="text-xs text-gray-400 mt-1">{helper}</p>}
    </div>
  );

  // Textarea component
  const Textarea = ({ label, value, onChange, placeholder, rows = 3 }) => (
    <div className="mb-4">
      <label className="text-sm text-gray-700 mb-2 block">{label}</label>
      <textarea
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        rows={rows}
        className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 outline-none focus:border-gray-400 transition-colors resize-none"
      />
    </div>
  );

  // Join access selector
  const JoinAccessSelector = () => (
    <div className="mb-4">
      <label className="text-sm text-gray-700 mb-3 block">Кто может вступить?</label>
      <div className="space-y-2">
        {!isIndependent && (
          <button
            onClick={() => setJoinAccess('club')}
            className={`w-full px-4 py-3 border rounded-xl text-left flex items-center gap-3 transition-colors ${
              joinAccess === 'club' 
                ? 'border-gray-800 bg-gray-50' 
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
              joinAccess === 'club' ? 'border-gray-800' : 'border-gray-300'
            }`}>
              {joinAccess === 'club' && <div className="w-2 h-2 rounded-full bg-gray-800" />}
            </div>
            <div>
              <p className="text-sm text-gray-800">Все участники клуба</p>
              <p className="text-xs text-gray-500">Члены клуба могут вступить</p>
            </div>
          </button>
        )}
        
        <button
          onClick={() => setJoinAccess('invite')}
          className={`w-full px-4 py-3 border rounded-xl text-left flex items-center gap-3 transition-colors ${
            joinAccess === 'invite' 
              ? 'border-gray-800 bg-gray-50' 
              : 'border-gray-200 hover:border-gray-300'
          }`}
        >
          <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
            joinAccess === 'invite' ? 'border-gray-800' : 'border-gray-300'
          }`}>
            {joinAccess === 'invite' && <div className="w-2 h-2 rounded-full bg-gray-800" />}
          </div>
          <div>
            <p className="text-sm text-gray-800">Только по приглашению</p>
            <p className="text-xs text-gray-500">Нужна ссылка для вступления</p>
          </div>
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-white flex flex-col max-w-md mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-4 border-b border-gray-200 sticky top-0 bg-white z-10">
        <button className="text-gray-500 text-sm hover:text-gray-700">
          ✕ Отмена
        </button>
        <span className="text-base font-medium text-gray-800">Новая группа</span>
        <div className="w-16" />
      </div>

      {/* Form */}
      <div className="flex-1 overflow-auto px-4 py-4">
        <Input
          label="Название группы"
          value={name}
          onChange={setName}
          placeholder="Вечерние интервалы"
          error={errors.name}
          required
        />

        <Textarea
          label="Описание"
          value={description}
          onChange={setDescription}
          placeholder="Скоростные тренировки по вторникам и четвергам"
          rows={4}
        />

        <div className="border-t border-gray-200 my-4" />

        {/* Club selector */}
        <div className="mb-4">
          <label className="text-sm text-gray-700 mb-2 block">Часть клуба?</label>
          <button
            onClick={() => !isIndependent && setShowClubPicker(true)}
            disabled={isIndependent}
            className={`w-full px-4 py-3 border rounded-xl text-sm text-left flex items-center justify-between transition-colors ${
              isIndependent 
                ? 'border-gray-100 bg-gray-50 text-gray-400' 
                : errors.club 
                  ? 'border-red-300 bg-red-50 text-gray-800'
                  : 'border-gray-200 text-gray-800 hover:border-gray-300'
            }`}
          >
            <span className={selectedClub && !isIndependent ? 'text-gray-800' : 'text-gray-400'}>
              {isIndependent ? '—' : getSelectedClubName()}
            </span>
            {!isIndependent && <span className="text-gray-400">▾</span>}
          </button>
          
          {/* Independent checkbox */}
          <label className="flex items-center gap-2 mt-3 cursor-pointer">
            <input
              type="checkbox"
              checked={isIndependent}
              onChange={toggleIndependent}
              className="w-4 h-4 rounded border-gray-300"
            />
            <span className="text-sm text-gray-600">Независимая группа</span>
          </label>
        </div>

        <div className="border-t border-gray-200 my-4" />

        <Input
          label="Telegram чат группы"
          value={telegramChat}
          onChange={setTelegramChat}
          placeholder="@srg_intervals"
          helper="Можно использовать тот же чат, что у клуба"
        />

        <div className="border-t border-gray-200 my-4" />

        <JoinAccessSelector />
      </div>

      {/* Submit button */}
      <div className="px-4 pb-6 pt-2 border-t border-gray-200">
        <button
          onClick={handleSubmit}
          className="w-full py-4 bg-gray-800 text-white rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors"
        >
          Создать группу
        </button>
      </div>

      {/* Club picker */}
      {showClubPicker && <ClubPicker />}
    </div>
  );
}
