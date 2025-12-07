import React, { useState } from 'react';

const sportTypes = [
  { id: 'running', icon: '🏃', label: 'Бег' },
  { id: 'trail', icon: '⛰️', label: 'Трейл' },
  { id: 'hiking', icon: '🥾', label: 'Хайкинг' },
  { id: 'cycling', icon: '🚴', label: 'Вело' }
];

export default function AydaRunCreateClub() {
  // Form state
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [selectedSports, setSelectedSports] = useState([]);
  const [telegramChat, setTelegramChat] = useState('');
  const [visibility, setVisibility] = useState('public'); // 'public' | 'private'
  const [errors, setErrors] = useState({});
  const [isCreated, setIsCreated] = useState(false);
  const [shareLink, setShareLink] = useState('');

  // Toggle sport selection
  const toggleSport = (sportId) => {
    setSelectedSports(prev => 
      prev.includes(sportId)
        ? prev.filter(id => id !== sportId)
        : [...prev, sportId]
    );
  };

  // Validation
  const validate = () => {
    const newErrors = {};
    if (!name.trim()) newErrors.name = true;
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Submit
  const handleSubmit = () => {
    if (validate()) {
      // Simulate creation
      setShareLink('https://t.me/aydarun_bot?start=club_abc123');
      setIsCreated(true);
    }
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
            Клуб создан!
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
            Перейти в клуб →
          </button>
        </div>
      </div>
    );
  }

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

  // Sport type chips (multi-select)
  const SportTypeChips = () => (
    <div className="mb-4">
      <label className="text-sm text-gray-700 mb-2 block">Виды активностей</label>
      <div className="flex flex-wrap gap-2">
        {sportTypes.map(sport => (
          <button
            key={sport.id}
            onClick={() => toggleSport(sport.id)}
            className={`px-4 py-2 rounded-lg border text-sm flex items-center gap-2 transition-colors ${
              selectedSports.includes(sport.id)
                ? 'border-gray-800 bg-gray-800 text-white'
                : 'border-gray-200 text-gray-600 hover:border-gray-300'
            }`}
          >
            <span>{sport.icon}</span>
            <span>{sport.label}</span>
          </button>
        ))}
      </div>
    </div>
  );

  // Visibility selector
  const VisibilitySelector = () => (
    <div className="mb-4">
      <label className="text-sm text-gray-700 mb-3 block">Видимость</label>
      <div className="space-y-2">
        <button
          onClick={() => setVisibility('public')}
          className={`w-full px-4 py-3 border rounded-xl text-left flex items-center gap-3 transition-colors ${
            visibility === 'public' 
              ? 'border-gray-800 bg-gray-50' 
              : 'border-gray-200 hover:border-gray-300'
          }`}
        >
          <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
            visibility === 'public' ? 'border-gray-800' : 'border-gray-300'
          }`}>
            {visibility === 'public' && <div className="w-2 h-2 rounded-full bg-gray-800" />}
          </div>
          <div>
            <p className="text-sm text-gray-800">Публичный</p>
            <p className="text-xs text-gray-500">Все могут найти и вступить</p>
          </div>
        </button>
        
        <button
          onClick={() => setVisibility('private')}
          className={`w-full px-4 py-3 border rounded-xl text-left flex items-center gap-3 transition-colors ${
            visibility === 'private' 
              ? 'border-gray-800 bg-gray-50' 
              : 'border-gray-200 hover:border-gray-300'
          }`}
        >
          <div className={`w-4 h-4 rounded-full border-2 flex items-center justify-center ${
            visibility === 'private' ? 'border-gray-800' : 'border-gray-300'
          }`}>
            {visibility === 'private' && <div className="w-2 h-2 rounded-full bg-gray-800" />}
          </div>
          <div>
            <p className="text-sm text-gray-800">По ссылке</p>
            <p className="text-xs text-gray-500">Только по приглашению</p>
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
        <span className="text-base font-medium text-gray-800">Новый клуб</span>
        <div className="w-16" />
      </div>

      {/* Form */}
      <div className="flex-1 overflow-auto px-4 py-4">
        <Input
          label="Название клуба"
          value={name}
          onChange={setName}
          placeholder="Trail Runners Almaty"
          error={errors.name}
          required
        />

        <Textarea
          label="Описание"
          value={description}
          onChange={setDescription}
          placeholder="Бегаем по горам вокруг Алматы. Все уровни подготовки приветствуются!"
          rows={4}
        />

        <SportTypeChips />

        <div className="border-t border-gray-200 my-4" />

        <Input
          label="Telegram чат клуба"
          value={telegramChat}
          onChange={setTelegramChat}
          placeholder="@trailrunners_almaty"
          helper="Бот будет отправлять уведомления о тренировках"
        />

        <div className="border-t border-gray-200 my-4" />

        <VisibilitySelector />
      </div>

      {/* Submit button */}
      <div className="px-4 pb-6 pt-2 border-t border-gray-200">
        <button
          onClick={handleSubmit}
          className="w-full py-4 bg-gray-800 text-white rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors"
        >
          Создать клуб
        </button>
      </div>
    </div>
  );
}
