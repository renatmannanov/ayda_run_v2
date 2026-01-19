const fs = require('fs');
const path = require('path');

const YEARS = [2022, 2023, 2024, 2025, 2026];

// Список из картинки
const officialList = [
  'Aitkazin Madiyar',
  'Akbayeva Madina',
  'Baikashev Shyngys',
  'Chernyshov Ivan',
  'Dunenbayev Nurzhan',
  'Gali Amir',
  'Iskhakova Aigerim',
  'Krasnov Ivan',
  'Krukhmalyov Vladimir',
  'Matveev Nikita',
  'Sakhiyev Zhandos',
  'Shatnaya Yekaterina',
  'Shilov Ivan',
  'Valiulina Diana',
  'Yashin Alexandr',
  'Tursunov Arman',
  'Petrova Elena',
  'Kairatov Damir',
  'Zhaksylyk Ayan',
  'Muratova Alia',
  'Ospanov Baurzhan',
  'Sagyndyk Asel',
  'Doszhanov Timur',
  'Kaliyeva Dana',
  'Serikbayev Aibek'
];

const data = {};
YEARS.forEach(year => {
  data[year] = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'data', year + '.json'), 'utf8'));
});

console.log('ПРОВЕРКА ОФИЦИАЛЬНОГО СПИСКА ВЕТЕРАНОВ 5 ГОНОК:\n');

let allGood = [];
let problems = [];

officialList.forEach(officialName => {
  const searchParts = officialName.toLowerCase().split(' ');

  let yearsWithFinish = [];
  let yearDetails = {};

  YEARS.forEach(year => {
    const found = data[year].participants.filter(p => {
      if (!p.name) return false;
      const pName = p.name.toLowerCase();
      return searchParts.every(part => pName.includes(part));
    });

    const finished = found.filter(p => p.finishTimeSeconds);

    if (finished.length > 0) {
      yearsWithFinish.push(year);
      const clubs = [...new Set(finished.map(p => p.club || '(нет)'))];
      yearDetails[year] = clubs.join(', ');
    } else if (found.length > 0) {
      yearDetails[year] = 'НЕ ФИНИШ';
    } else {
      yearDetails[year] = 'НЕТ';
    }
  });

  if (yearsWithFinish.length === 5) {
    allGood.push({ name: officialName, details: yearDetails });
  } else {
    problems.push({
      name: officialName,
      count: yearsWithFinish.length,
      years: yearsWithFinish,
      details: yearDetails
    });
  }
});

console.log('✅ ПОДТВЕРЖДЕНО (все 5 гонок): ' + allGood.length + ' человек\n');
allGood.forEach(p => {
  console.log('  ' + p.name);
  YEARS.forEach(y => console.log('    ' + y + ': ' + p.details[y]));
});

console.log('\n\n❌ ПРОБЛЕМЫ (не все 5 гонок): ' + problems.length + ' человек\n');
problems.forEach(p => {
  console.log('  ' + p.name + ' - только ' + p.count + ' гонок (' + p.years.join(', ') + ')');
  YEARS.forEach(y => {
    const mark = p.years.includes(y) ? '✓' : '✗';
    console.log('    ' + mark + ' ' + y + ': ' + p.details[y]);
  });
  console.log('');
});
