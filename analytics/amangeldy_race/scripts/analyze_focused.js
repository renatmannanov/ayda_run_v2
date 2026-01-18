/**
 * Фокусированная аналитика Amangeldy Race
 * Участники и Клубы
 */

const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, '..', 'data');
const OUTPUT_DIR = path.join(__dirname, '..', 'output');

const YEARS = [2022, 2023, 2024, 2025, 2026];

// Загружаем данные всех годов
function loadAllYears() {
  const data = {};
  YEARS.forEach(year => {
    const file = path.join(DATA_DIR, `${year}.json`);
    data[year] = JSON.parse(fs.readFileSync(file, 'utf8'));
  });
  return data;
}

// Нормализация названий клубов
function normalizeClubName(club) {
  if (!club) return null;
  return club
    .replace(/&quot;/g, '"')
    .replace(/\s+/g, ' ')
    .trim();
}

// Нормализация названий дистанций
function normalizeDistanceName(distance) {
  if (!distance) return null;
  // 2022 использовал полные названия, потом перешли на сокращения
  const mapping = {
    'Vertical Kilometer 1000': 'VK 1000',
    'SkySprint 600': 'SS 600',
    'SkyRace 1500': 'SR 1500',
    'SkyRace 1400': 'SR 1400'
  };
  return mapping[distance] || distance;
}

// =====================================================
// УЧАСТНИКИ
// =====================================================

function analyzeParticipants(data) {
  console.log('\n📊 АНАЛИЗ УЧАСТНИКОВ\n');

  // Считаем УНИКАЛЬНЫХ участников по имени для каждого года
  const uniqueStatsByYear = {};
  YEARS.forEach(year => {
    const seenNames = new Set();
    let registered = 0;
    let finished = 0;
    let men = 0;
    let women = 0;

    data[year].participants.forEach(p => {
      if (!p.name) return;
      const name = p.name.toLowerCase().trim();

      if (!seenNames.has(name)) {
        seenNames.add(name);
        registered++;

        if (p.finishTimeSeconds) {
          finished++;
          if (p.gender === 'M') men++;
          if (p.gender === 'F') women++;
        }
      }
    });

    uniqueStatsByYear[year] = { registered, finished, men, women };
  });

  // 1. Рекорд 2026
  const record2026 = uniqueStatsByYear[2026].registered;

  // 2. Динамика роста участников за 5 лет
  const participantsDynamics = YEARS.map(year => {
    const stats = uniqueStatsByYear[year];
    return {
      year,
      registered: stats.registered,
      finished: stats.finished,
      finishRate: Math.round(stats.finished / stats.registered * 100)
    };
  });

  // Рост год к году
  const growthYoY = [];
  for (let i = 1; i < YEARS.length; i++) {
    const prev = participantsDynamics[i - 1].registered;
    const curr = participantsDynamics[i].registered;
    growthYoY.push({
      period: `${YEARS[i - 1]}-${YEARS[i]}`,
      growth: curr - prev,
      growthPercent: Math.round((curr - prev) / prev * 100)
    });
  }

  // Общий рост с 2022
  const totalGrowth = {
    from: participantsDynamics[0].registered,
    to: participantsDynamics[4].registered,
    growth: participantsDynamics[4].registered - participantsDynamics[0].registered,
    growthPercent: Math.round((participantsDynamics[4].registered - participantsDynamics[0].registered) / participantsDynamics[0].registered * 100)
  };

  // 3-4. Женщины - динамика (уникальные)
  const womenDynamics = YEARS.map(year => {
    const stats = uniqueStatsByYear[year];
    return {
      year,
      women: stats.women,
      total: stats.finished,
      womenPercent: Math.round(stats.women / stats.finished * 100 * 10) / 10
    };
  });

  // Рост женщин год к году
  const womenGrowthYoY = [];
  for (let i = 1; i < YEARS.length; i++) {
    const prev = womenDynamics[i - 1].women;
    const curr = womenDynamics[i].women;
    womenGrowthYoY.push({
      period: `${YEARS[i - 1]}-${YEARS[i]}`,
      growth: curr - prev,
      growthPercent: Math.round((curr - prev) / prev * 100)
    });
  }

  const womenTotalGrowth = {
    from: womenDynamics[0].women,
    to: womenDynamics[4].women,
    growth: womenDynamics[4].women - womenDynamics[0].women,
    growthPercent: Math.round((womenDynamics[4].women - womenDynamics[0].women) / womenDynamics[0].women * 100),
    shareFrom: womenDynamics[0].womenPercent,
    shareTo: womenDynamics[4].womenPercent
  };

  // 5. Ветераны - участники 4-5 гонок
  const participantsByName = {};

  YEARS.forEach(year => {
    data[year].participants
      .filter(p => p.finishTimeSeconds && p.name)
      .forEach(p => {
        const name = p.name.toLowerCase().trim();
        if (!participantsByName[name]) {
          participantsByName[name] = {
            name: p.name,
            years: [],
            clubs: {},
            gender: p.gender
          };
        }
        participantsByName[name].years.push(year);
        if (p.club) {
          const club = normalizeClubName(p.club);
          participantsByName[name].clubs[year] = club;
        }
      });
  });

  // Ветераны 5 гонок
  const veterans5 = Object.values(participantsByName)
    .filter(p => p.years.length === 5)
    .map(p => {
      // Берём последний известный клуб
      const lastClub = p.clubs[2026] || p.clubs[2025] || p.clubs[2024] || p.clubs[2023] || p.clubs[2022] || null;
      return {
        name: p.name,
        club: lastClub,
        gender: p.gender,
        participations: 5
      };
    })
    .sort((a, b) => (a.club || 'zzz').localeCompare(b.club || 'zzz'));

  // Ветераны 4 гонок
  const veterans4 = Object.values(participantsByName)
    .filter(p => p.years.length === 4)
    .map(p => {
      const lastClub = p.clubs[2026] || p.clubs[2025] || p.clubs[2024] || p.clubs[2023] || p.clubs[2022] || null;
      return {
        name: p.name,
        club: lastClub,
        gender: p.gender,
        participations: 4,
        years: p.years
      };
    })
    .sort((a, b) => (a.club || 'zzz').localeCompare(b.club || 'zzz'));

  // 6. Новички по годам
  const allSeenNames = new Set();
  const newcomersByYear = [];

  YEARS.forEach(year => {
    const yearNames = new Set();
    data[year].participants
      .filter(p => p.finishTimeSeconds && p.name)
      .forEach(p => {
        const name = p.name.toLowerCase().trim();
        yearNames.add(name);
      });

    const newcomers = [...yearNames].filter(name => !allSeenNames.has(name)).length;
    const returning = [...yearNames].filter(name => allSeenNames.has(name)).length;
    const total = yearNames.size;

    newcomersByYear.push({
      year,
      newcomers,
      returning,
      total,
      newcomersPercent: Math.round(newcomers / total * 100),
      returningPercent: Math.round(returning / total * 100)
    });

    // Добавляем всех участников этого года в общий set
    yearNames.forEach(name => allSeenNames.add(name));
  });

  return {
    record2026,
    participantsDynamics,
    growthYoY,
    totalGrowth,
    womenDynamics,
    womenGrowthYoY,
    womenTotalGrowth,
    newcomersByYear,
    veterans: {
      fiveRaces: veterans5,
      fiveRacesCount: veterans5.length,
      fourRaces: veterans4,
      fourRacesCount: veterans4.length,
      fourPlusTotal: veterans5.length + veterans4.length
    }
  };
}

// =====================================================
// КЛУБЫ
// =====================================================

function analyzeClubs(data) {
  console.log('\n🏃 АНАЛИЗ КЛУБОВ\n');

  // Собираем статистику по клубам за все годы
  const clubStatsByYear = {};
  const allClubs = new Set();

  YEARS.forEach(year => {
    clubStatsByYear[year] = {};
    const seenInClub = {}; // track unique participants per club

    data[year].participants
      .filter(p => p.finishTimeSeconds && p.club && p.name)
      .forEach(p => {
        const club = normalizeClubName(p.club);
        const name = p.name.toLowerCase().trim();
        allClubs.add(club);

        if (!clubStatsByYear[year][club]) {
          clubStatsByYear[year][club] = {
            total: 0,
            men: 0,
            women: 0
          };
          seenInClub[club] = new Set();
        }

        // Count only unique participants
        if (!seenInClub[club].has(name)) {
          seenInClub[club].add(name);
          clubStatsByYear[year][club].total++;
          if (p.gender === 'M') clubStatsByYear[year][club].men++;
          if (p.gender === 'F') clubStatsByYear[year][club].women++;
        }
      });
  });

  // 1. Количество клубов 2026
  const clubs2026Count = Object.keys(clubStatsByYear[2026]).length;

  // 2. Количество уникальных клубов за всё время
  const uniqueClubsTotal = allClubs.size;

  // 3. Динамика роста клубов по годам
  const clubsDynamics = YEARS.map(year => ({
    year,
    clubsCount: Object.keys(clubStatsByYear[year]).length
  }));

  // Рост клубов год к году
  const clubsGrowthYoY = [];
  for (let i = 1; i < YEARS.length; i++) {
    const prev = clubsDynamics[i - 1].clubsCount;
    const curr = clubsDynamics[i].clubsCount;
    clubsGrowthYoY.push({
      period: `${YEARS[i - 1]}-${YEARS[i]}`,
      growth: curr - prev,
      growthPercent: Math.round((curr - prev) / prev * 100)
    });
  }

  // 4. Топ 10 клубов по годам
  const top10ByYear = {};
  YEARS.forEach(year => {
    top10ByYear[year] = Object.entries(clubStatsByYear[year])
      .map(([club, stats]) => ({
        club,
        total: stats.total,
        men: stats.men,
        women: stats.women,
        womenPercent: stats.total > 0 ? Math.round(stats.women / stats.total * 100) : 0
      }))
      .sort((a, b) => b.total - a.total)
      .slice(0, 10);
  });

  // Определяем топ-10 клубов 2026 для детального анализа
  const top10Clubs2026 = top10ByYear[2026].map(c => c.club);

  // 5. Рост участников в топ-10 клубах за 5 лет
  const top10ClubsGrowth = top10Clubs2026.map(club => {
    const history = YEARS.map(year => {
      const stats = clubStatsByYear[year][club];
      return {
        year,
        total: stats ? stats.total : 0,
        men: stats ? stats.men : 0,
        women: stats ? stats.women : 0
      };
    });

    // Находим первый год участия
    const firstYearData = history.find(h => h.total > 0);
    const lastYearData = history[history.length - 1];

    let growth = null;
    let growthPercent = null;
    if (firstYearData && firstYearData.total > 0) {
      growth = lastYearData.total - firstYearData.total;
      growthPercent = Math.round((lastYearData.total - firstYearData.total) / firstYearData.total * 100);
    }

    return {
      club,
      history,
      firstYear: firstYearData ? history.indexOf(firstYearData) + 2022 : null,
      growth,
      growthPercent,
      total2026: lastYearData.total
    };
  });

  // 6. Рост доли женщин в топ-10 клубах
  const top10ClubsWomenGrowth = top10Clubs2026.map(club => {
    const history = YEARS.map(year => {
      const stats = clubStatsByYear[year][club];
      if (!stats || stats.total === 0) {
        return { year, women: 0, total: 0, womenPercent: null };
      }
      return {
        year,
        women: stats.women,
        total: stats.total,
        womenPercent: Math.round(stats.women / stats.total * 100)
      };
    });

    // Первый и последний год с данными
    const withData = history.filter(h => h.total > 0);
    const first = withData[0];
    const last = withData[withData.length - 1];

    let shareGrowth = null;
    if (first && last && first.womenPercent !== null && last.womenPercent !== null) {
      shareGrowth = last.womenPercent - first.womenPercent;
    }

    return {
      club,
      history,
      womenShareGrowth: shareGrowth,
      women2026: last ? last.women : 0,
      womenPercent2026: last ? last.womenPercent : 0
    };
  });

  return {
    clubs2026Count,
    uniqueClubsTotal,
    clubsDynamics,
    clubsGrowthYoY,
    top10ByYear,
    top10ClubsGrowth,
    top10ClubsWomenGrowth
  };
}

// =====================================================
// ДИСТАНЦИИ
// =====================================================

function analyzeDistances(data) {
  console.log('\n📏 АНАЛИЗ ДИСТАНЦИЙ\n');

  const distanceStatsByYear = {};
  const allDistances = new Set();

  YEARS.forEach(year => {
    distanceStatsByYear[year] = {};
    const seenByDistance = {}; // track unique participants per distance

    data[year].participants
      .filter(p => p.finishTimeSeconds && p.distance && p.name)
      .forEach(p => {
        const distance = normalizeDistanceName(p.distance);
        const name = p.name.toLowerCase().trim();
        allDistances.add(distance);

        if (!distanceStatsByYear[year][distance]) {
          distanceStatsByYear[year][distance] = {
            total: 0,
            men: 0,
            women: 0,
            clubs: new Set()
          };
          seenByDistance[distance] = new Set();
        }

        // Count only unique participants per distance
        if (!seenByDistance[distance].has(name)) {
          seenByDistance[distance].add(name);
          distanceStatsByYear[year][distance].total++;
          if (p.gender === 'M') distanceStatsByYear[year][distance].men++;
          if (p.gender === 'F') distanceStatsByYear[year][distance].women++;
          if (p.club) {
            distanceStatsByYear[year][distance].clubs.add(normalizeClubName(p.club));
          }
        }
      });
  });

  // Преобразуем Set в число клубов
  YEARS.forEach(year => {
    Object.keys(distanceStatsByYear[year]).forEach(distance => {
      distanceStatsByYear[year][distance].clubsCount = distanceStatsByYear[year][distance].clubs.size;
      delete distanceStatsByYear[year][distance].clubs;
    });
  });

  // Динамика по дистанциям
  const distancesByYear = YEARS.map(year => {
    const distances = Object.entries(distanceStatsByYear[year])
      .map(([distance, stats]) => ({
        distance,
        total: stats.total,
        men: stats.men,
        women: stats.women,
        womenPercent: stats.total > 0 ? Math.round(stats.women / stats.total * 100) : 0,
        clubsCount: stats.clubsCount
      }))
      .sort((a, b) => b.total - a.total);

    return { year, distances };
  });

  // Рост по каждой дистанции за 5 лет
  const distanceGrowth = {};
  allDistances.forEach(distance => {
    const history = YEARS.map(year => {
      const stats = distanceStatsByYear[year][distance];
      return {
        year,
        total: stats ? stats.total : 0,
        men: stats ? stats.men : 0,
        women: stats ? stats.women : 0,
        clubsCount: stats ? stats.clubsCount : 0
      };
    });

    const first = history.find(h => h.total > 0);
    const last = history[history.length - 1];

    let growthPercent = null;
    if (first && first.total > 0 && last.total > 0) {
      growthPercent = Math.round((last.total - first.total) / first.total * 100);
    }

    distanceGrowth[distance] = {
      history,
      growthPercent
    };
  });

  return {
    distancesByYear,
    distanceGrowth,
    allDistances: [...allDistances].sort()
  };
}

// =====================================================
// ГЛАВНАЯ ФУНКЦИЯ
// =====================================================

function main() {
  console.log('📊 Amangeldy Race - Фокусированная аналитика');
  console.log('   Участники и Клубы\n');
  console.log('='.repeat(50));

  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  const data = loadAllYears();
  console.log('✅ Данные загружены');

  const participants = analyzeParticipants(data);
  const clubs = analyzeClubs(data);
  const distances = analyzeDistances(data);

  const analytics = {
    generatedAt: new Date().toISOString(),
    eventName: 'AMANGELDY RACE',

    participants,
    clubs,
    distances
  };

  // Сохраняем
  const outputFile = path.join(OUTPUT_DIR, 'participants_clubs_analytics.json');
  fs.writeFileSync(outputFile, JSON.stringify(analytics, null, 2), 'utf8');
  console.log(`\n✅ Сохранено: ${outputFile}`);

  // Выводим ключевые цифры
  printSummary(analytics);
}

function printSummary(a) {
  console.log('\n' + '='.repeat(60));
  console.log('📊 УЧАСТНИКИ');
  console.log('='.repeat(60));

  console.log('\n1️⃣  РЕКОРД 2026: ' + a.participants.record2026 + ' участников');

  console.log('\n2️⃣  ДИНАМИКА РОСТА УЧАСТНИКОВ:');
  console.log('─'.repeat(40));
  a.participants.participantsDynamics.forEach(d => {
    console.log(`   ${d.year}: ${d.registered} зарегистрировано → ${d.finished} финишировали (${d.finishRate}%)`);
  });
  console.log('─'.repeat(40));
  console.log(`   ИТОГО рост: ${a.participants.totalGrowth.from} → ${a.participants.totalGrowth.to} (+${a.participants.totalGrowth.growthPercent}%)`);

  console.log('\n   Рост по годам:');
  a.participants.growthYoY.forEach(g => {
    console.log(`   ${g.period}: +${g.growth} (+${g.growthPercent}%)`);
  });

  console.log('\n3️⃣  ЖЕНЩИНЫ - ДИНАМИКА:');
  console.log('─'.repeat(40));
  a.participants.womenDynamics.forEach(d => {
    console.log(`   ${d.year}: ${d.women} женщин (${d.womenPercent}% от финишёров)`);
  });
  console.log('─'.repeat(40));
  console.log(`   ИТОГО рост: ${a.participants.womenTotalGrowth.from} → ${a.participants.womenTotalGrowth.to} (+${a.participants.womenTotalGrowth.growthPercent}%)`);
  console.log(`   Доля: ${a.participants.womenTotalGrowth.shareFrom}% → ${a.participants.womenTotalGrowth.shareTo}%`);

  console.log('\n4️⃣  ВЕТЕРАНЫ (4-5 гонок): ' + a.participants.veterans.fourPlusTotal + ' человек');
  console.log(`   • 5 гонок: ${a.participants.veterans.fiveRacesCount} человек`);
  console.log(`   • 4 гонки: ${a.participants.veterans.fourRacesCount} человек`);

  console.log('\n   Ветераны 5 гонок:');
  a.participants.veterans.fiveRaces.forEach(v => {
    console.log(`   • ${v.name} (${v.club || 'без клуба'})`);
  });

  console.log('\n5️⃣  НОВИЧКИ ПО ГОДАМ:');
  console.log('─'.repeat(40));
  a.participants.newcomersByYear.forEach(d => {
    console.log(`   ${d.year}: ${d.newcomers} новичков (${d.newcomersPercent}%), ${d.returning} вернулись (${d.returningPercent}%)`);
  });

  console.log('\n' + '='.repeat(60));
  console.log('🏃 КЛУБЫ');
  console.log('='.repeat(60));

  console.log('\n1️⃣  КЛУБОВ В 2026: ' + a.clubs.clubs2026Count);
  console.log('2️⃣  УНИКАЛЬНЫХ КЛУБОВ ЗА ВСЁ ВРЕМЯ: ' + a.clubs.uniqueClubsTotal);

  console.log('\n3️⃣  ДИНАМИКА РОСТА КЛУБОВ:');
  console.log('─'.repeat(40));
  a.clubs.clubsDynamics.forEach(d => {
    console.log(`   ${d.year}: ${d.clubsCount} клубов`);
  });

  console.log('\n4️⃣  ТОП-10 КЛУБОВ ПО ГОДАМ:');
  YEARS.forEach(year => {
    console.log(`\n   ${year}:`);
    a.clubs.top10ByYear[year].forEach((c, i) => {
      console.log(`   ${i + 1}. ${c.club}: ${c.total} (М:${c.men} Ж:${c.women}, ${c.womenPercent}% жен)`);
    });
  });

  console.log('\n5️⃣  РОСТ УЧАСТНИКОВ В ТОП-10 КЛУБАХ 2026:');
  console.log('─'.repeat(40));
  a.clubs.top10ClubsGrowth.forEach(c => {
    const historyStr = c.history.map(h => h.total).join(' → ');
    console.log(`   ${c.club}:`);
    console.log(`      ${historyStr}`);
    if (c.growthPercent !== null) {
      console.log(`      Рост: ${c.growth > 0 ? '+' : ''}${c.growth} (${c.growthPercent > 0 ? '+' : ''}${c.growthPercent}%)`);
    }
  });

  console.log('\n6️⃣  ДОЛЯ ЖЕНЩИН В ТОП-10 КЛУБАХ:');
  console.log('─'.repeat(40));
  a.clubs.top10ClubsWomenGrowth.forEach(c => {
    const historyStr = c.history.map(h => h.womenPercent !== null ? h.womenPercent + '%' : '-').join(' → ');
    console.log(`   ${c.club}:`);
    console.log(`      ${historyStr}`);
    if (c.womenShareGrowth !== null) {
      console.log(`      Изменение доли: ${c.womenShareGrowth > 0 ? '+' : ''}${c.womenShareGrowth}%`);
    }
  });

  console.log('\n' + '='.repeat(60));
  console.log('📏 ДИСТАНЦИИ');
  console.log('='.repeat(60));

  console.log('\n1️⃣  УЧАСТНИКИ ПО ДИСТАНЦИЯМ ПО ГОДАМ:');
  a.distances.distancesByYear.forEach(({ year, distances }) => {
    console.log(`\n   ${year}:`);
    distances.forEach(d => {
      console.log(`   • ${d.distance}: ${d.total} участников (М:${d.men} Ж:${d.women}, ${d.womenPercent}% жен), ${d.clubsCount} клубов`);
    });
  });

  console.log('\n2️⃣  РОСТ ПО ДИСТАНЦИЯМ ЗА 5 ЛЕТ:');
  console.log('─'.repeat(40));
  Object.entries(a.distances.distanceGrowth).forEach(([distance, data]) => {
    const historyStr = data.history.map(h => h.total).join(' → ');
    console.log(`   ${distance}: ${historyStr}`);
    if (data.growthPercent !== null) {
      console.log(`      Рост: ${data.growthPercent > 0 ? '+' : ''}${data.growthPercent}%`);
    }
  });

  console.log('\n✨ Готово!');
}

main();
