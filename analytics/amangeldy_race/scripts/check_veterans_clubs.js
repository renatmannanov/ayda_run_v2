const fs = require('fs');
const path = require('path');

const YEARS = [2022, 2023, 2024, 2025, 2026];
const data = {};
YEARS.forEach(year => {
  data[year] = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'data', year + '.json'), 'utf8'));
});

const participantsByName = {};

YEARS.forEach(year => {
  data[year].participants
    .filter(p => p.finishTimeSeconds && p.name)
    .forEach(p => {
      const name = p.name.toLowerCase().trim();
      if (!participantsByName[name]) {
        participantsByName[name] = {
          name: p.name,
          clubs: {}
        };
      }
      if (!participantsByName[name].clubs[year]) {
        participantsByName[name].clubs[year] = p.club || null;
      }
    });
});

const veterans5 = Object.values(participantsByName)
  .filter(p => Object.keys(p.clubs).length === 5)
  .sort((a, b) => a.name.localeCompare(b.name));

console.log('ВЕТЕРАНЫ 5 ГОНОК - ИСТОРИЯ КЛУБОВ:\n');
veterans5.forEach(v => {
  console.log('--- ' + v.name + ' ---');
  YEARS.forEach(year => {
    const club = v.clubs[year];
    console.log('  ' + year + ': ' + (club || '(без клуба)'));
  });

  // Проверяем на изменения клубов
  const uniqueClubs = [...new Set(Object.values(v.clubs).filter(c => c))];
  if (uniqueClubs.length > 1) {
    console.log('  ⚠️  МЕНЯЛ КЛУБ: ' + uniqueClubs.join(' -> '));
  }
  console.log('');
});
