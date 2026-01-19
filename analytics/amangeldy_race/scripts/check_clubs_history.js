const fs = require('fs');
const path = require('path');

const YEARS = [2022, 2023, 2024, 2025, 2026];

const data = {};
YEARS.forEach(year => {
  data[year] = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'data', year + '.json'), 'utf8'));
});

// Собираем участников по уникальным годам финиша с полной историей клубов
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
          clubsByYear: {},
          gender: p.gender
        };
      }
      participantsByName[name].yearsSet.add(year);
      // Храним ВСЕ клубы за год (может быть несколько записей)
      if (!participantsByName[name].clubsByYear[year]) {
        participantsByName[name].clubsByYear[year] = new Set();
      }
      participantsByName[name].clubsByYear[year].add(p.club || '(нет)');
    });
});

// Фильтруем только 5-гоночных
const veterans5 = Object.values(participantsByName)
  .filter(p => p.yearsSet.size === 5)
  .sort((a, b) => a.name.localeCompare(b.name));

console.log('ВЕТЕРАНЫ 5 ГОНОК - ПОЛНАЯ ИСТОРИЯ КЛУБОВ:\n');
console.log('='.repeat(80));

veterans5.forEach(p => {
  console.log('\n' + p.name);
  console.log('-'.repeat(40));

  const allClubs = new Set();
  YEARS.forEach(year => {
    const clubs = [...(p.clubsByYear[year] || ['НЕТ'])];
    clubs.forEach(c => { if (c !== '(нет)') allClubs.add(c); });
    console.log(`  ${year}: ${clubs.join(', ')}`);
  });

  // Определяем "последний" клуб (2026 -> 2025 -> ...)
  let lastClub = null;
  for (let i = YEARS.length - 1; i >= 0; i--) {
    const year = YEARS[i];
    const clubs = [...(p.clubsByYear[year] || [])].filter(c => c !== '(нет)');
    if (clubs.length > 0) {
      lastClub = clubs[0];
      break;
    }
  }

  // Проверяем на смену клубов
  const uniqueClubs = [...allClubs];
  if (uniqueClubs.length > 1) {
    console.log(`  ⚠️  МЕНЯЛ КЛУБ: ${uniqueClubs.join(' / ')}`);
  } else if (uniqueClubs.length === 1) {
    console.log(`  ✅ Клуб: ${uniqueClubs[0]}`);
  } else {
    console.log(`  — Без клуба`);
  }
  console.log(`  → В отчёте будет: ${lastClub || '(без клуба)'}`);
});

// Проверяем конкретно людей с HomeRun
console.log('\n\n' + '='.repeat(80));
console.log('ПРОВЕРКА HOMERUN УЧАСТНИКОВ:');
console.log('='.repeat(80));

Object.values(participantsByName)
  .filter(p => {
    // Ищем всех кто хоть раз был в HomeRun
    return Object.values(p.clubsByYear).some(clubs =>
      [...clubs].some(c => c && c.toLowerCase().includes('homerun'))
    );
  })
  .sort((a, b) => b.yearsSet.size - a.yearsSet.size)
  .slice(0, 20)
  .forEach(p => {
    console.log('\n' + p.name + ' (' + p.yearsSet.size + ' гонок)');
    YEARS.forEach(year => {
      if (p.clubsByYear[year]) {
        console.log(`  ${year}: ${[...p.clubsByYear[year]].join(', ')}`);
      }
    });
  });
