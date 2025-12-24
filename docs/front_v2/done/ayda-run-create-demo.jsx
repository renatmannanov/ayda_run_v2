import React, { useState } from 'react';

// ============================================
// SHARED COMPONENTS
// ============================================
const SectionLabel = ({ children }) => (
  <label className="block text-sm font-medium text-gray-700 mb-2">{children}</label>
);

const TextInput = ({ placeholder, value, onChange, hint }) => (
  <div>
    <input
      type="text"
      placeholder={placeholder}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-gray-400"
    />
    {hint && <p className="text-xs text-gray-400 mt-1.5">{hint}</p>}
  </div>
);

const TextArea = ({ placeholder, value, onChange, rows = 3 }) => (
  <textarea
    placeholder={placeholder}
    value={value}
    onChange={(e) => onChange(e.target.value)}
    rows={rows}
    className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-gray-400 resize-none"
  />
);

const ToggleButtons = ({ options, selected, onChange, hint }) => (
  <div>
    <div className="flex gap-2">
      {options.map(option => (
        <button
          key={option.id}
          onClick={() => onChange(option.id)}
          className={`flex items-center gap-2 px-4 py-2.5 rounded-full text-sm transition-colors ${
            selected === option.id
              ? 'bg-gray-800 text-white'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
          }`}
        >
          {option.icon && <span>{option.icon}</span>}
          {option.label}
        </button>
      ))}
    </div>
    {hint && <p className="text-xs text-gray-400 mt-2">{hint}</p>}
  </div>
);

const DropdownPicker = ({ value, options, onChange, placeholder }) => {
  const [isOpen, setIsOpen] = useState(false);
  const selectedOption = options.find(o => o.id === value);

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 border border-gray-200 rounded-xl text-sm text-left flex items-center justify-between hover:border-gray-300 transition-colors"
      >
        <div className="flex items-center gap-2">
          {selectedOption?.icon && <span>{selectedOption.icon}</span>}
          <span className={selectedOption ? 'text-gray-800' : 'text-gray-400'}>
            {selectedOption?.label || placeholder}
          </span>
          {selectedOption?.sublabel && (
            <span className="text-gray-400">· {selectedOption.sublabel}</span>
          )}
        </div>
        <svg className={`w-5 h-5 text-gray-400 transition-transform ${isOpen ? 'rotate-180' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      
      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          <div className="absolute top-full left-0 right-0 mt-1 bg-white border border-gray-200 rounded-xl shadow-lg z-20 overflow-hidden">
            {options.map(option => (
              <button
                key={option.id}
                onClick={() => {
                  onChange(option.id);
                  setIsOpen(false);
                }}
                className={`w-full px-4 py-3 text-sm text-left flex items-center gap-2 hover:bg-gray-50 transition-colors ${
                  value === option.id ? 'bg-gray-50' : ''
                }`}
              >
                {option.icon && <span>{option.icon}</span>}
                <div>
                  <span className="text-gray-800">{option.label}</span>
                  {option.sublabel && (
                    <span className="text-gray-400 ml-1">· {option.sublabel}</span>
                  )}
                </div>
                {value === option.id && (
                  <svg className="w-5 h-5 text-gray-800 ml-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                  </svg>
                )}
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

const CreateHeader = ({ title, onClose }) => (
  <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200">
    <button onClick={onClose} className="text-gray-500 hover:text-gray-700 flex items-center gap-1">
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
      </svg>
      <span className="text-sm">Отмена</span>
    </button>
    <h1 className="text-base font-medium text-gray-800">{title}</h1>
    <div className="w-16" />
  </div>
);

const SubmitButton = ({ children, onClick }) => (
  <div className="px-4 py-4 border-t border-gray-200 bg-white">
    <button
      onClick={onClick}
      className="w-full py-4 bg-gray-800 text-white rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors"
    >
      {children}
    </button>
  </div>
);

const FixedAccess = ({ icon, label, hint }) => (
  <div>
    <div className="flex gap-2">
      <div className="flex items-center gap-2 px-4 py-2.5 rounded-full text-sm bg-gray-800 text-white">
        {icon && <span>{icon}</span>}
        <span>{label}</span>
      </div>
    </div>
    {hint && <p className="text-xs text-gray-400 mt-2">{hint}</p>}
  </div>
);

// ============================================
// GPX UPLOAD POPUP
// ============================================
const GPXUploadPopup = ({ 
  isOpen, 
  onClose, 
  onSkip, 
  onUpload,
  mode = 'create', // 'create' | 'add' | 'edit'
  existingFile = null 
}) => {
  const [file, setFile] = useState(existingFile);

  if (!isOpen) return null;

  const handleFileSelect = (e) => {
    const selectedFile = e.target.files?.[0];
    if (selectedFile && selectedFile.name.endsWith('.gpx')) {
      setFile({
        name: selectedFile.name,
        size: (selectedFile.size / 1024).toFixed(1) + ' KB'
      });
    }
  };

  const getTitle = () => {
    switch (mode) {
      case 'edit': return 'Изменить GPX';
      case 'add': return 'Добавить GPX';
      default: return 'Добавить маршрут';
    }
  };

  const getDescription = () => {
    switch (mode) {
      case 'edit': return 'Загрузите новый GPX файл для замены текущего маршрута';
      case 'add': return 'Загрузите GPX файл с маршрутом тренировки';
      default: return 'Хотите добавить GPX файл с маршрутом? Это поможет участникам лучше подготовиться.';
    }
  };

  const getSubmitText = () => {
    if (!file) return mode === 'create' ? 'Пропустить' : 'Отмена';
    switch (mode) {
      case 'edit': return 'Сохранить';
      case 'add': return 'Добавить';
      default: return 'Готово';
    }
  };

  const handleSubmit = () => {
    if (file) {
      onUpload(file);
    } else if (mode === 'create') {
      onSkip?.();
    } else {
      onClose();
    }
  };

  const handleRemoveFile = () => {
    setFile(null);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-black/30"
        onClick={onClose}
      />
      
      {/* Bottom Sheet */}
      <div className="relative bg-white rounded-t-2xl w-full max-w-md overflow-hidden">
        {/* Header */}
        <div className="px-4 pt-4 pb-2">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-medium text-gray-800">{getTitle()}</h3>
            <button 
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 p-1"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          <p className="text-sm text-gray-500 mt-1">{getDescription()}</p>
        </div>
        
        {/* Content */}
        <div className="px-4 py-4">
          {!file ? (
            /* Upload button */
            <label className="block border border-gray-200 rounded-xl p-4 text-center cursor-pointer hover:bg-gray-50 transition-colors">
              <input
                type="file"
                accept=".gpx"
                onChange={handleFileSelect}
                className="hidden"
              />
              <div className="text-2xl mb-2">📍</div>
              <p className="text-sm text-gray-600 font-medium">Выбрать GPX файл</p>
            </label>
          ) : (
            /* File preview */
            <div className="border border-gray-200 rounded-xl p-4">
              <div className="flex items-start gap-3">
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-lg">📍</span>
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-800 truncate">{file.name}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{file.size}</p>
                </div>
                <button
                  onClick={handleRemoveFile}
                  className="text-gray-400 hover:text-gray-600 p-1"
                >
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
            </div>
          )}
        </div>
        
        {/* Actions */}
        <div className="px-4 pb-8 flex gap-3">
          {mode === 'create' && !file && (
            <button
              onClick={onSkip}
              className="flex-1 py-3 text-sm text-gray-500 hover:text-gray-700 transition-colors"
            >
              Пропустить
            </button>
          )}
          <button
            onClick={handleSubmit}
            className={`flex-1 py-3 rounded-xl text-sm font-medium transition-colors ${
              file
                ? 'bg-gray-800 text-white hover:bg-gray-700'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {getSubmitText()}
          </button>
        </div>
      </div>
    </div>
  );
};

// ============================================
// SUCCESS MESSAGE (after activity creation)
// ============================================
const SuccessMessage = ({ onDone }) => (
  <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
    <div className="absolute inset-0 bg-black/40" />
    <div className="relative bg-white rounded-2xl w-full max-w-sm p-6 text-center">
      <div className="text-5xl mb-4">✅</div>
      <h3 className="text-lg font-medium text-gray-800">Тренировка создана!</h3>
      <p className="text-sm text-gray-500 mt-2">Участники смогут записаться на неё</p>
      <button
        onClick={onDone}
        className="w-full mt-6 py-3 bg-gray-800 text-white rounded-xl text-sm font-medium hover:bg-gray-700 transition-colors"
      >
        Готово
      </button>
    </div>
  </div>
);

// ============================================
// SAMPLE DATA
// ============================================
const userClubs = [
  { id: 1, name: "SRG Almaty", icon: "🏆" },
  { id: 2, name: "Club Runners", icon: "🏃" },
];

const userGroups = [
  { id: 1, name: "Горные бегуны", clubId: 1, clubName: "SRG Almaty" },
  { id: 2, name: "Утренние интервалы", clubId: 1, clubName: "SRG Almaty" },
];

const sportTypes = [
  { id: 'run', icon: '🏃', name: 'Бег' },
  { id: 'trail', icon: '⛰️', name: 'Трейл' },
  { id: 'hike', icon: '🥾', name: 'Хайкинг' },
  { id: 'bike', icon: '🚴', name: 'Вело' },
];

const SportPills = ({ selected, onChange }) => (
  <div className="flex flex-wrap gap-2">
    {sportTypes.map(sport => (
      <button
        key={sport.id}
        onClick={() => {
          onChange(prev => 
            prev.includes(sport.id)
              ? prev.filter(id => id !== sport.id)
              : [...prev, sport.id]
          );
        }}
        className={`flex items-center gap-1.5 px-3 py-2 rounded-full text-sm transition-colors ${
          selected.includes(sport.id)
            ? 'bg-gray-800 text-white'
            : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
        }`}
      >
        <span>{sport.icon}</span>
        <span>{sport.name}</span>
      </button>
    ))}
  </div>
);

// ============================================
// CREATE ACTIVITY SCREEN
// ============================================
const CreateActivityScreen = ({ onClose }) => {
  const [title, setTitle] = useState('');
  const [visibility, setVisibility] = useState('public');
  const [access, setAccess] = useState('open');
  const [flowStep, setFlowStep] = useState('form'); // 'form' | 'gpx' | 'success'
  const [gpxFile, setGpxFile] = useState(null);

  const visibilityOptions = [
    { id: 'public', icon: '🌐', label: 'Публичная', sublabel: 'видят все' },
    ...userClubs.map(club => ({
      id: `club_${club.id}`,
      icon: club.icon,
      label: club.name,
      sublabel: 'клуб'
    })),
    ...userGroups.map(group => ({
      id: `group_${group.id}`,
      icon: '👥',
      label: group.name,
      sublabel: group.clubName
    })),
  ];

  const accessOptions = [
    { id: 'open', label: 'Все желающие' },
    { id: 'request', icon: '🔒', label: 'По заявке' },
  ];

  const getAccessHint = () => {
    if (access === 'open') {
      return visibility === 'public' 
        ? 'Любой может записаться на тренировку'
        : 'Любой участник может записаться';
    }
    return 'Нужно одобрение организатора';
  };

  const handleCreate = () => {
    // After form submission, show GPX popup
    setFlowStep('gpx');
  };

  const handleGpxUpload = (file) => {
    setGpxFile(file);
    setFlowStep('success');
  };

  const handleGpxSkip = () => {
    setFlowStep('success');
  };

  const handleDone = () => {
    // Reset and close
    setFlowStep('form');
    setTitle('');
    setVisibility('public');
    setAccess('open');
    setGpxFile(null);
  };

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <CreateHeader title="Новая активность" onClose={onClose} />
      
      <div className="flex-1 overflow-auto p-4 space-y-6">
        <div>
          <SectionLabel>Название</SectionLabel>
          <TextInput 
            placeholder="Например: Длинная в горы"
            value={title}
            onChange={setTitle}
          />
        </div>

        <div>
          <SectionLabel>Видимость</SectionLabel>
          <DropdownPicker
            value={visibility}
            options={visibilityOptions}
            onChange={setVisibility}
            placeholder="Выбрать..."
          />
        </div>

        <div>
          <SectionLabel>Кто может записаться?</SectionLabel>
          <ToggleButtons
            options={accessOptions}
            selected={access}
            onChange={setAccess}
            hint={getAccessHint()}
          />
        </div>
      </div>

      <SubmitButton onClick={handleCreate}>Создать тренировку</SubmitButton>

      {/* GPX Upload Popup */}
      <GPXUploadPopup
        isOpen={flowStep === 'gpx'}
        onClose={() => setFlowStep('form')}
        onSkip={handleGpxSkip}
        onUpload={handleGpxUpload}
        mode="create"
      />

      {/* Success Message */}
      {flowStep === 'success' && (
        <SuccessMessage onDone={handleDone} />
      )}
    </div>
  );
};

// ============================================
// CREATE CLUB SCREEN
// ============================================
const CreateClubScreen = ({ onClose }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [sports, setSports] = useState([]);
  const [telegramChat, setTelegramChat] = useState('');
  const [visibility, setVisibility] = useState('public');
  const [access, setAccess] = useState('open');

  const handleVisibilityChange = (newVisibility) => {
    setVisibility(newVisibility);
    if (newVisibility === 'private') {
      setAccess('request');
    }
  };

  const visibilityOptions = [
    { id: 'public', icon: '🌐', label: 'Публичный', sublabel: 'все могут найти' },
    { id: 'private', icon: '🔒', label: 'Закрытый', sublabel: 'только по заявке' },
  ];

  const accessOptions = [
    { id: 'open', label: 'Все желающие' },
    { id: 'request', icon: '🔒', label: 'По заявке' },
  ];

  const getAccessHint = () => {
    if (visibility === 'private') {
      return 'Закрытый клуб — вступление только по заявке';
    }
    if (access === 'open') {
      return 'Любой может вступить в клуб';
    }
    return 'Нужно одобрение администратора';
  };

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <CreateHeader title="Новый клуб" onClose={onClose} />
      
      <div className="flex-1 overflow-auto p-4 space-y-6">
        <div>
          <SectionLabel>Название</SectionLabel>
          <TextInput 
            placeholder="Например: Trail Runners Almaty"
            value={name}
            onChange={setName}
          />
        </div>

        <div>
          <SectionLabel>Описание</SectionLabel>
          <TextArea
            placeholder="Расскажите о клубе..."
            value={description}
            onChange={setDescription}
          />
        </div>

        <div>
          <SectionLabel>Виды спорта</SectionLabel>
          <SportPills selected={sports} onChange={setSports} />
        </div>

        <div>
          <SectionLabel>Telegram чат клуба</SectionLabel>
          <TextInput 
            placeholder="@trailrunners_almaty"
            value={telegramChat}
            onChange={setTelegramChat}
            hint="Бот будет отправлять уведомления о тренировках"
          />
        </div>

        <div>
          <SectionLabel>Видимость</SectionLabel>
          <DropdownPicker
            value={visibility}
            options={visibilityOptions}
            onChange={handleVisibilityChange}
            placeholder="Выбрать..."
          />
        </div>

        <div>
          <SectionLabel>Кто может вступить?</SectionLabel>
          {visibility === 'private' ? (
            <FixedAccess
              icon="🔒"
              label="По заявке"
              hint={getAccessHint()}
            />
          ) : (
            <ToggleButtons
              options={accessOptions}
              selected={access}
              onChange={setAccess}
              hint={getAccessHint()}
            />
          )}
        </div>
      </div>

      <SubmitButton>Создать клуб</SubmitButton>
    </div>
  );
};

// ============================================
// CREATE GROUP SCREEN
// ============================================
const CreateGroupScreen = ({ onClose }) => {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [telegramChat, setTelegramChat] = useState('');
  const [visibility, setVisibility] = useState('public');
  const [access, setAccess] = useState('open');

  const visibilityOptions = [
    { id: 'public', icon: '🌐', label: 'Публичная', sublabel: 'видят все' },
    ...userClubs.map(club => ({
      id: `club_${club.id}`,
      icon: club.icon,
      label: club.name,
      sublabel: 'только участники клуба'
    })),
  ];

  const accessOptions = [
    { id: 'open', label: 'Все желающие' },
    { id: 'request', icon: '🔒', label: 'По заявке' },
  ];

  const getAccessHint = () => {
    if (access === 'open') {
      return visibility === 'public'
        ? 'Любой может вступить в группу'
        : 'Любой участник клуба может вступить';
    }
    return 'Нужно одобрение администратора';
  };

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <CreateHeader title="Новая группа" onClose={onClose} />
      
      <div className="flex-1 overflow-auto p-4 space-y-6">
        <div>
          <SectionLabel>Название</SectionLabel>
          <TextInput 
            placeholder="Например: Утренние интервалы"
            value={name}
            onChange={setName}
          />
        </div>

        <div>
          <SectionLabel>Описание</SectionLabel>
          <TextArea
            placeholder="Расскажите о группе..."
            value={description}
            onChange={setDescription}
          />
        </div>

        <div>
          <SectionLabel>Telegram чат группы</SectionLabel>
          <TextInput 
            placeholder="@srg_intervals"
            value={telegramChat}
            onChange={setTelegramChat}
            hint="Можно использовать тот же чат, что у клуба"
          />
        </div>

        <div>
          <SectionLabel>Видимость</SectionLabel>
          <DropdownPicker
            value={visibility}
            options={visibilityOptions}
            onChange={setVisibility}
            placeholder="Выбрать..."
          />
        </div>

        <div>
          <SectionLabel>Кто может вступить?</SectionLabel>
          <ToggleButtons
            options={accessOptions}
            selected={access}
            onChange={setAccess}
            hint={getAccessHint()}
          />
        </div>
      </div>

      <SubmitButton>Создать группу</SubmitButton>
    </div>
  );
};

// ============================================
// DEMO WITH SWITCHER
// ============================================
export default function CreateScreensDemo() {
  const [screen, setScreen] = useState('activity');
  const [gpxPopupMode, setGpxPopupMode] = useState(null); // null | 'add' | 'edit'

  return (
    <div className="min-h-screen bg-gray-100 max-w-md mx-auto">
      {/* Switcher */}
      <div className="bg-white border-b border-gray-200 px-4 py-2">
        <div className="flex justify-center gap-2 mb-2">
          <button
            onClick={() => setScreen('activity')}
            className={`text-xs px-3 py-1.5 rounded-lg transition-colors ${
              screen === 'activity' ? 'bg-gray-800 text-white' : 'bg-gray-100 text-gray-600'
            }`}
          >
            Активность
          </button>
          <button
            onClick={() => setScreen('club')}
            className={`text-xs px-3 py-1.5 rounded-lg transition-colors ${
              screen === 'club' ? 'bg-gray-800 text-white' : 'bg-gray-100 text-gray-600'
            }`}
          >
            Клуб
          </button>
          <button
            onClick={() => setScreen('group')}
            className={`text-xs px-3 py-1.5 rounded-lg transition-colors ${
              screen === 'group' ? 'bg-gray-800 text-white' : 'bg-gray-100 text-gray-600'
            }`}
          >
            Группа
          </button>
        </div>
        
        {/* GPX Popup demos */}
        <div className="flex justify-center gap-2 pt-2 border-t border-gray-100">
          <span className="text-xs text-gray-400 py-1.5">GPX:</span>
          <button
            onClick={() => setGpxPopupMode('add')}
            className="text-xs px-3 py-1.5 rounded-lg bg-gray-100 text-gray-600 hover:bg-gray-200"
          >
            Добавить
          </button>
          <button
            onClick={() => setGpxPopupMode('edit')}
            className="text-xs px-3 py-1.5 rounded-lg bg-gray-100 text-gray-600 hover:bg-gray-200"
          >
            Изменить
          </button>
        </div>
      </div>
      
      {/* Screen */}
      {screen === 'activity' && <CreateActivityScreen onClose={() => {}} />}
      {screen === 'club' && <CreateClubScreen onClose={() => {}} />}
      {screen === 'group' && <CreateGroupScreen onClose={() => {}} />}

      {/* GPX Popup demos */}
      <GPXUploadPopup
        isOpen={gpxPopupMode === 'add'}
        onClose={() => setGpxPopupMode(null)}
        onUpload={(file) => { console.log('Uploaded:', file); setGpxPopupMode(null); }}
        mode="add"
      />
      <GPXUploadPopup
        isOpen={gpxPopupMode === 'edit'}
        onClose={() => setGpxPopupMode(null)}
        onUpload={(file) => { console.log('Updated:', file); setGpxPopupMode(null); }}
        mode="edit"
        existingFile={{ name: 'medeu_trail.gpx', size: '124.5 KB' }}
      />
    </div>
  );
}
