import React, { useState } from 'react';

const sportTypes = [
  { id: 'running', icon: '🏃', label: 'Бег' },
  { id: 'trail', icon: '⛰️', label: 'Трейл' },
  { id: 'hiking', icon: '🥾', label: 'Хайкинг' },
  { id: 'cycling', icon: '🚴', label: 'Вело' }
];

const difficultyLevels = [
  { id: 'easy', label: 'Легкая' },
  { id: 'medium', label: 'Средняя' },
  { id: 'hard', label: 'Сложная' }
];

const sampleClubsGroups = [
  { id: 1, name: 'SRG Almaty', type: 'club', groups: [
    { id: 101, name: 'Утренние бегуны' },
    { id: 102, name: 'Горные бегуны' }
  ]},
  { id: 2, name: 'Trail Nomads', type: 'club', groups: [] },
  { id: 104, name: 'Горные велосипедисты', type: 'group', groups: [] }
];

export default function AydaRunCreateActivity() {
  // Form state
  const [title, setTitle] = useState('');
  const [date, setDate] = useState('');
  const [time, setTime] = useState('07:00');
  const [location, setLocation] = useState('');
  const [sportType, setSportType] = useState('running');
  const [distance, setDistance] = useState('');
  const [elevation, setElevation] = useState('');
  const [duration, setDuration] = useState('');
  const [difficulty, setDifficulty] = useState('medium');
  const [maxParticipants, setMaxParticipants] = useState('20');
  const [noLimit, setNoLimit] = useState(false);
  const [description, setDescription] = useState('');
  const [gpxFile, setGpxFile] = useState(null);
  const [selectedClub, setSelectedClub] = useState('');
  const [selectedGroup, setSelectedGroup] = useState('');
  const [isPublic, setIsPublic] = useState(false);
  
  const [showDifficultyPicker, setShowDifficultyPicker] = useState(false);
  const [showClubPicker, setShowClubPicker] = useState(false);
  const [errors, setErrors] = useState({});

  // Validation
  const validate = () => {
    const newErrors = {};
    if (!title.trim()) newErrors.title = true;
    if (!date) newErrors.date = true;
    if (!location.trim()) newErrors.location = true;
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Submit
  const handleSubmit = () => {
    if (validate()) {
      alert('Тренировка создана!');
    }
  };

  // Get selected club object
  const getSelectedClubObj = () => {
    return sampleClubsGroups.find(c => c.id.toString() === selectedClub);
  };

  // Format club/group display
  const getClubGroupDisplay = () => {
    if (isPublic) return 'Публичная (видят все)';
    if (!selectedClub) return 'Выбрать...';
    const club = getSelectedClubObj();
    if (!club) return 'Выбрать...';
    if (selectedGroup) {
      const group = club.groups?.find(g => g.id.toString() === selectedGroup);
      return `${club.name} / ${group?.name || ''}`;
    }
    return club.name;
  };

  // Input component
  const Input = ({ label, value, onChange, placeholder, error, required, type = 'text', suffix }) => (
    <div className="mb-4">
      <label className="text-sm text-gray-700 mb-2 block">
        {label} {required && <span className="text-red-400">*</span>}
      </label>
      <div className="relative">
        <input
          type={type}
          value={value}
          onChange={(e) => onChange(e.target.value)}
          placeholder={placeholder}
          className={`w-full px-4 py-3 border rounded-xl text-sm text-gray-800 placeholder-gray-400 outline-none transition-colors ${
            error ? 'border-red-300 bg-red-50' : 'border-gray-200 focus:border-gray-400'
          }`}
        />
        {suffix && (
          <span className="absolute right-4 top-1/2 -translate-y-1/2 text-sm text-gray-400">
            {suffix}
          </span>
        )}
      </div>
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

  // Sport type chips
  const SportTypeChips = () => (
    <div className="mb-4">
      <label className="text-sm text-gray-700 mb-2 block">Тип</label>
      <div className="flex flex-wrap gap-2">
        {sportTypes.map(sport => (
          <button
            key={sport.id}
            onClick={() => setSportType(sport.id)}
            className={`px-4 py-2 rounded-lg border text-sm flex items-center gap-2 transition-colors ${
              sportType === sport.id
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

  // Difficulty picker popup
  const DifficultyPicker = () => (
    <div 
      className="fixed inset-0 bg-black/30 z-50 flex items-end justify-center"
      onClick={() => setShowDifficultyPicker(false)}
    >
      <div 
        className="bg-white w-full max-w-md rounded-t-2xl p-6"
        onClick={e => e.stopPropagation()}
      >
        <h3 className="text-base font-medium text-gray-800 mb-4">Сложность</h3>
        {difficultyLevels.map(level => (
          <button
            key={level.id}
            onClick={() => {
              setDifficulty(level.id);
              setShowDifficultyPicker(false);
            }}
            className={`w-full text-left py-3 px-2 rounded-lg transition-colors ${
              difficulty === level.id ? 'bg-gray-100' : 'hover:bg-gray-50'
            }`}
          >
            <span className="text-sm text-gray-700">{level.label}</span>
          </button>
        ))}
        <button
          onClick={() => setShowDifficultyPicker(false)}
          className="w-full mt-4 py-3 text-gray-400 text-sm"
        >
          Отмена
        </button>
      </div>
    </div>
  );

  // Club/Group picker popup
  const ClubGroupPicker = () => (
    <div 
      className="fixed inset-0 bg-black/30 z-50 flex items-end justify-center"
      onClick={() => setShowClubPicker(false)}
    >
      <div 
        className="bg-white w-full max-w-md rounded-t-2xl p-6 max-h-[70vh] overflow-auto"
        onClick={e => e.stopPropagation()}
      >
        <h3 className="text-base font-medium text-gray-800 mb-4">Клуб / Группа</h3>
        
        {/* Public option */}
        <button
          onClick={() => {
            setIsPublic(true);
            setSelectedClub('');
            setSelectedGroup('');
            setShowClubPicker(false);
          }}
          className={`w-full text-left py-3 px-2 rounded-lg mb-2 transition-colors ${
            isPublic ? 'bg-gray-100' : 'hover:bg-gray-50'
          }`}
        >
          <span className="text-sm text-gray-700">🌍 Публичная (видят все)</span>
        </button>
        
        <div className="border-t border-gray-200 my-3" />
        
        {sampleClubsGroups.map(club => (
          <div key={club.id} className="mb-2">
            <button
              onClick={() => {
                setIsPublic(false);
                setSelectedClub(club.id.toString());
                setSelectedGroup('');
                if (club.groups.length === 0) {
                  setShowClubPicker(false);
                }
              }}
              className={`w-full text-left py-3 px-2 rounded-lg transition-colors ${
                selectedClub === club.id.toString() && !selectedGroup ? 'bg-gray-100' : 'hover:bg-gray-50'
              }`}
            >
              <span className="text-sm text-gray-700">
                {club.type === 'club' ? '🏆' : '👥'} {club.name}
              </span>
            </button>
            
            {/* Groups within club */}
            {club.groups.length > 0 && selectedClub === club.id.toString() && (
              <div className="ml-6 mt-1">
                {club.groups.map(group => (
                  <button
                    key={group.id}
                    onClick={() => {
                      setSelectedGroup(group.id.toString());
                      setShowClubPicker(false);
                    }}
                    className={`w-full text-left py-2 px-2 rounded-lg transition-colors ${
                      selectedGroup === group.id.toString() ? 'bg-gray-100' : 'hover:bg-gray-50'
                    }`}
                  >
                    <span className="text-sm text-gray-600">→ {group.name}</span>
                  </button>
                ))}
              </div>
            )}
          </div>
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

  const getDifficultyLabel = () => {
    return difficultyLevels.find(d => d.id === difficulty)?.label || 'Средняя';
  };

  return (
    <div className="min-h-screen bg-white flex flex-col max-w-md mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-4 border-b border-gray-200 sticky top-0 bg-white z-10">
        <button className="text-gray-500 text-sm hover:text-gray-700">
          ✕ Отмена
        </button>
        <span className="text-base font-medium text-gray-800">Новая тренировка</span>
        <div className="w-16" /> {/* Spacer */}
      </div>

      {/* Form */}
      <div className="flex-1 overflow-auto px-4 py-4">
        <Input
          label="Название"
          value={title}
          onChange={setTitle}
          placeholder="Утренняя пробежка"
          error={errors.title}
          required
        />

        {/* Date & Time */}
        <div className="flex gap-3 mb-4">
          <div className="flex-1">
            <label className="text-sm text-gray-700 mb-2 block">
              Когда <span className="text-red-400">*</span>
            </label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className={`w-full px-4 py-3 border rounded-xl text-sm text-gray-800 outline-none transition-colors ${
                errors.date ? 'border-red-300 bg-red-50' : 'border-gray-200 focus:border-gray-400'
              }`}
            />
          </div>
          <div className="w-28">
            <label className="text-sm text-gray-700 mb-2 block">&nbsp;</label>
            <input
              type="time"
              value={time}
              onChange={(e) => setTime(e.target.value)}
              className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 outline-none focus:border-gray-400 transition-colors"
            />
          </div>
        </div>

        <Input
          label="Где"
          value={location}
          onChange={setLocation}
          placeholder="Центральный парк, фонтан"
          error={errors.location}
          required
        />

        <SportTypeChips />

        <div className="border-t border-gray-200 my-4" />

        {/* Stats row */}
        <div className="flex gap-3 mb-4">
          <div className="flex-1">
            <label className="text-sm text-gray-700 mb-2 block">Дистанция</label>
            <div className="relative">
              <input
                type="number"
                value={distance}
                onChange={(e) => setDistance(e.target.value)}
                placeholder="10"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 outline-none focus:border-gray-400 transition-colors pr-12"
              />
              <span className="absolute right-4 top-1/2 -translate-y-1/2 text-sm text-gray-400">км</span>
            </div>
          </div>
          <div className="flex-1">
            <label className="text-sm text-gray-700 mb-2 block">Набор</label>
            <div className="relative">
              <input
                type="number"
                value={elevation}
                onChange={(e) => setElevation(e.target.value)}
                placeholder="150"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 outline-none focus:border-gray-400 transition-colors pr-10"
              />
              <span className="absolute right-4 top-1/2 -translate-y-1/2 text-sm text-gray-400">м</span>
            </div>
          </div>
        </div>

        <div className="flex gap-3 mb-4">
          <div className="flex-1">
            <label className="text-sm text-gray-700 mb-2 block">Длительность</label>
            <input
              type="text"
              value={duration}
              onChange={(e) => setDuration(e.target.value)}
              placeholder="~1 час"
              className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 outline-none focus:border-gray-400 transition-colors"
            />
          </div>
          <div className="flex-1">
            <label className="text-sm text-gray-700 mb-2 block">Сложность</label>
            <button
              onClick={() => setShowDifficultyPicker(true)}
              className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 text-left flex items-center justify-between hover:border-gray-300 transition-colors"
            >
              <span>{getDifficultyLabel()}</span>
              <span className="text-gray-400">▾</span>
            </button>
          </div>
        </div>

        {/* Max participants */}
        <div className="mb-4">
          <label className="text-sm text-gray-700 mb-2 block">Макс. участников</label>
          <div className="flex items-center gap-3">
            <input
              type="number"
              value={maxParticipants}
              onChange={(e) => setMaxParticipants(e.target.value)}
              disabled={noLimit}
              className={`w-24 px-4 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 outline-none focus:border-gray-400 transition-colors ${
                noLimit ? 'bg-gray-50 text-gray-400' : ''
              }`}
            />
            <label className="flex items-center gap-2 text-sm text-gray-600">
              <input
                type="checkbox"
                checked={noLimit}
                onChange={(e) => setNoLimit(e.target.checked)}
                className="w-4 h-4 rounded border-gray-300"
              />
              Без лимита
            </label>
          </div>
        </div>

        <div className="border-t border-gray-200 my-4" />

        <Textarea
          label="Описание"
          value={description}
          onChange={setDescription}
          placeholder="Разминка у фонтана, потом 2 круга по парку. Берите воду!"
          rows={4}
        />

        {/* GPX upload */}
        <div className="mb-4">
          <label className="text-sm text-gray-700 mb-2 block">Маршрут GPX</label>
          <button className="px-4 py-3 border border-dashed border-gray-300 rounded-xl text-sm text-gray-500 hover:border-gray-400 hover:text-gray-600 transition-colors w-full text-left">
            + Добавить файл
          </button>
        </div>

        <div className="border-t border-gray-200 my-4" />

        {/* Club/Group selector */}
        <div className="mb-4">
          <label className="text-sm text-gray-700 mb-2 block">Клуб / Группа</label>
          <button
            onClick={() => setShowClubPicker(true)}
            className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm text-gray-800 text-left flex items-center justify-between hover:border-gray-300 transition-colors"
          >
            <span className={isPublic || selectedClub ? 'text-gray-800' : 'text-gray-400'}>
              {getClubGroupDisplay()}
            </span>
            <span className="text-gray-400">▾</span>
          </button>
        </div>
      </div>

      {/* Submit button */}
      <div className="px-4 pb-6 pt-2 border-t border-gray-200">
        <button
          onClick={handleSubmit}
          className="w-full py-4 bg-gray-800 text-white rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors"
        >
          Создать тренировку
        </button>
      </div>

      {/* Pickers */}
      {showDifficultyPicker && <DifficultyPicker />}
      {showClubPicker && <ClubGroupPicker />}
    </div>
  );
}
