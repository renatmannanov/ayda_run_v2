const fs = require('fs');
const path = require('path');

const YEARS = [2022, 2023, 2024, 2025, 2026];

const data = {};
YEARS.forEach(year => {
  data[year] = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'data', year + '.json'), 'utf8'));
});

// Собираем участников по уникальным годам финиша
const participantsByName = {};

YEARS.forEach(year => {
  data[year].participants
    .filter(p => p.finishTimeSeconds && p.name)
    .forEach(p => {
      const name = p.name.toLowerCase().trim();
      if (!participantsByName[name]) {
        participantsByName[name] = {
          name: p.name,
          yearsSet: new Set(),
          clubs: {},
          gender: p.gender
        };
      }
      participantsByName[name].yearsSet.add(year);
      if (p.club) {
        participantsByName[name].clubs[year] = p.club;
      }
    });
});

// Группируем по количеству гонок
const byRaceCount = {
  5: [],
  4: [],
  3: []
};

Object.values(participantsByName).forEach(p => {
  const count = p.yearsSet.size;
  if (count >= 3 && count <= 5) {
    const lastClub = p.clubs[2026] || p.clubs[2025] || p.clubs[2024] || p.clubs[2023] || p.clubs[2022] || null;
    byRaceCount[count].push({
      name: p.name,
      club: lastClub,
      years: [...p.yearsSet].sort(),
      gender: p.gender
    });
  }
});

// Сортируем по клубу, потом по имени
Object.keys(byRaceCount).forEach(count => {
  byRaceCount[count].sort((a, b) => {
    const clubA = a.club || 'яяя';
    const clubB = b.club || 'яяя';
    if (clubA !== clubB) return clubA.localeCompare(clubB);
    return a.name.localeCompare(b.name);
  });
});

console.log('='.repeat(60));
console.log('ВЕТЕРАНЫ 5 ГОНОК (все 5 лет): ' + byRaceCount[5].length + ' человек');
console.log('='.repeat(60));
byRaceCount[5].forEach(p => {
  console.log(`  ${p.name} | ${p.club || '(без клуба)'} | ${p.years.join(', ')}`);
});

console.log('\n' + '='.repeat(60));
console.log('ВЕТЕРАНЫ 4 ГОНОК: ' + byRaceCount[4].length + ' человек');
console.log('='.repeat(60));
byRaceCount[4].forEach(p => {
  console.log(`  ${p.name} | ${p.club || '(без клуба)'} | ${p.years.join(', ')}`);
});

console.log('\n' + '='.repeat(60));
console.log('ВЕТЕРАНЫ 3 ГОНОК: ' + byRaceCount[3].length + ' человек');
console.log('='.repeat(60));
byRaceCount[3].forEach(p => {
  console.log(`  ${p.name} | ${p.club || '(без клуба)'} | ${p.years.join(', ')}`);
});

console.log('\n\nИТОГО:');
console.log('  5 гонок: ' + byRaceCount[5].length);
console.log('  4 гонки: ' + byRaceCount[4].length);
console.log('  3 гонки: ' + byRaceCount[3].length);
