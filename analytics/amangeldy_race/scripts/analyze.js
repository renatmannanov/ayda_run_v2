/**
 * Расширенная аналитика Amangeldy Race
 * Генерирует интересные инсайты для соцсетей и маркетинга
 */

const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, '..', 'data');
const OUTPUT_DIR = path.join(__dirname, '..', 'output');

// Загружаем данные всех годов
function loadAllYears() {
  const years = [2022, 2023, 2024, 2025, 2026];
  const data = {};
  years.forEach(year => {
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

// Конвертация времени в секунды
function timeToSeconds(timeStr) {
  if (!timeStr) return null;
  const hmsMatch = timeStr.match(/(\d+)h(\d+)'(\d+)/);
  if (hmsMatch) {
    return parseInt(hmsMatch[1]) * 3600 + parseInt(hmsMatch[2]) * 60 + parseInt(hmsMatch[3]);
  }
  const colonMatch = timeStr.match(/(\d+):(\d+):(\d+)/);
  if (colonMatch) {
    return parseInt(colonMatch[1]) * 3600 + parseInt(colonMatch[2]) * 60 + parseInt(colonMatch[3]);
  }
  return null;
}

function secondsToTime(seconds) {
  if (seconds === null) return null;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.round(seconds % 60);
  if (h > 0) {
    return `${h}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  }
  return `${m}:${s.toString().padStart(2, '0')}`;
}

// 1. АНАЛИЗ РОСТА ПОПУЛЯРНОСТИ
function analyzeGrowth(data) {
  const years = [2022, 2023, 2024, 2025, 2026];
  const growth = years.map(year => ({
    year,
    registered: data[year].stats.totalRegistered,
    finished: data[year].stats.totalFinished,
    men: data[year].stats.byGender.M,
    women: data[year].stats.byGender.F,
    womenPercent: Math.round(data[year].stats.byGender.F / data[year].stats.totalFinished * 100),
    finishRate: Math.round(data[year].stats.totalFinished / data[year].stats.totalRegistered * 100)
  }));

  // Расчёт роста
  const totalGrowth = Math.round((growth[4].registered - growth[0].registered) / growth[0].registered * 100);
  const womenGrowth = Math.round((growth[4].women - growth[0].women) / growth[0].women * 100);

  return {
    yearByYear: growth,
    summary: {
      totalGrowthPercent: totalGrowth,
      womenGrowthPercent: womenGrowth,
      avgFinishRate: Math.round(growth.reduce((a, b) => a + b.finishRate, 0) / growth.length),
      recordParticipants2026: growth[4].registered,
      womenPercentage2026: growth[4].womenPercent
    }
  };
}

// 2. АНАЛИЗ ТОП КЛУБОВ
function analyzeClubs(data) {
  const clubStats = {};
  const years = [2022, 2023, 2024, 2025, 2026];

  years.forEach(year => {
    data[year].participants
      .filter(p => p.club && p.finishTimeSeconds)
      .forEach(p => {
        const club = normalizeClubName(p.club);
        if (!clubStats[club]) {
          clubStats[club] = {
            name: club,
            totalFinishers: 0,
            years: {},
            finishers: []
          };
        }
        clubStats[club].totalFinishers++;
        clubStats[club].years[year] = (clubStats[club].years[year] || 0) + 1;
        clubStats[club].finishers.push({
          year,
          name: p.name,
          time: p.finishTimeSeconds,
          distance: p.distance
        });
      });
  });

  // Топ клубов по общему числу участников
  const topClubs = Object.values(clubStats)
    .filter(c => c.totalFinishers >= 5)
    .sort((a, b) => b.totalFinishers - a.totalFinishers)
    .slice(0, 20);

  // Клубы с наибольшим ростом
  const clubsWithGrowth = Object.values(clubStats)
    .filter(c => c.years[2026] && c.years[2022])
    .map(c => ({
      name: c.name,
      growth: c.years[2026] - c.years[2022],
      growthPercent: Math.round((c.years[2026] - c.years[2022]) / c.years[2022] * 100),
      2022: c.years[2022] || 0,
      2026: c.years[2026] || 0
    }))
    .filter(c => c.growth > 0)
    .sort((a, b) => b.growth - a.growth)
    .slice(0, 10);

  // Клубы-новички 2026
  const newClubs2026 = Object.values(clubStats)
    .filter(c => c.years[2026] && !c.years[2025] && !c.years[2024] && !c.years[2023] && !c.years[2022])
    .sort((a, b) => b.years[2026] - a.years[2026])
    .slice(0, 10)
    .map(c => ({ name: c.name, participants: c.years[2026] }));

  return {
    topClubsAllTime: topClubs.map(c => ({
      name: c.name,
      total: c.totalFinishers,
      yearsActive: Object.keys(c.years).length
    })),
    clubsWithBiggestGrowth: clubsWithGrowth,
    newClubs2026,
    totalClubs2026: Object.values(clubStats).filter(c => c.years[2026]).length
  };
}

// 3. АНАЛИЗ "ВЕТЕРАНОВ" - УЧАСТНИКОВ ВСЕХ 5 ЛЕТ
function analyzeVeterans(data) {
  const participantsByName = {};
  const years = [2022, 2023, 2024, 2025, 2026];

  years.forEach(year => {
    data[year].participants
      .filter(p => p.finishTimeSeconds && p.name)
      .forEach(p => {
        const name = p.name.toLowerCase().trim();
        if (!participantsByName[name]) {
          participantsByName[name] = {
            name: p.name,
            years: {},
            club: p.club
          };
        }
        participantsByName[name].years[year] = {
          time: p.finishTimeSeconds,
          distance: p.distance,
          category: p.category
        };
        // Обновляем клуб на последний известный
        if (p.club) participantsByName[name].club = p.club;
      });
  });

  // Участники всех 5 лет
  const fiveYearVeterans = Object.values(participantsByName)
    .filter(p => Object.keys(p.years).length === 5)
    .map(p => ({
      name: p.name,
      club: normalizeClubName(p.club),
      participations: 5
    }));

  // Участники 4+ лет
  const fourPlusYearVeterans = Object.values(participantsByName)
    .filter(p => Object.keys(p.years).length >= 4)
    .length;

  // Уникальных участников за все время
  const totalUniqueParticipants = Object.keys(participantsByName).length;

  // Возвращающиеся участники 2026 (были хотя бы 1 раз раньше)
  const returningIn2026 = Object.values(participantsByName)
    .filter(p => p.years[2026] && Object.keys(p.years).length > 1)
    .length;

  const totalFinished2026 = data[2026].stats.totalFinished;

  return {
    fiveYearVeterans: fiveYearVeterans.slice(0, 30),
    fiveYearVeteransCount: fiveYearVeterans.length,
    fourPlusYearsCount: fourPlusYearVeterans,
    totalUniqueParticipants,
    returningParticipants2026: returningIn2026,
    returningPercent2026: Math.round(returningIn2026 / totalFinished2026 * 100),
    newParticipants2026: totalFinished2026 - returningIn2026,
    newParticipantsPercent2026: Math.round((totalFinished2026 - returningIn2026) / totalFinished2026 * 100)
  };
}

// 4. РЕКОРДЫ И ЛУЧШИЕ ВРЕМЕНА ПО ДИСТАНЦИЯМ
function analyzeRecords(data) {
  const years = [2022, 2023, 2024, 2025, 2026];
  const records = {};

  // Маппинг дистанций к стандартным названиям
  const distanceMapping = {
    'VK 1000': 'VK 1000',
    'Vertical Kilometer 1000': 'VK 1000',
    'SS 600': 'SS 600',
    'SkySprint 600': 'SS 600',
    'SR 1500': 'SR 1500',
    'SkyRace 1500': 'SR 1500',
    'SR 1400': 'SR 1400'
  };

  years.forEach(year => {
    data[year].participants
      .filter(p => p.finishTimeSeconds && p.distance)
      .forEach(p => {
        const dist = distanceMapping[p.distance] || p.distance;
        if (!dist || dist === 'Unknown') return;

        if (!records[dist]) {
          records[dist] = {
            distance: dist,
            allTime: { M: null, F: null },
            byYear: {}
          };
        }

        if (!records[dist].byYear[year]) {
          records[dist].byYear[year] = { M: null, F: null };
        }

        const gender = p.gender;
        if (!gender) return;

        const current = records[dist].byYear[year][gender];
        if (!current || p.finishTimeSeconds < current.time) {
          records[dist].byYear[year][gender] = {
            name: p.name,
            time: p.finishTimeSeconds,
            timeFormatted: secondsToTime(p.finishTimeSeconds),
            club: normalizeClubName(p.club)
          };
        }

        const allTime = records[dist].allTime[gender];
        if (!allTime || p.finishTimeSeconds < allTime.time) {
          records[dist].allTime[gender] = {
            name: p.name,
            time: p.finishTimeSeconds,
            timeFormatted: secondsToTime(p.finishTimeSeconds),
            year,
            club: normalizeClubName(p.club)
          };
        }
      });
  });

  return records;
}

// 5. ГЕОГРАФИЯ УЧАСТНИКОВ
function analyzeGeography(data) {
  const years = [2022, 2023, 2024, 2025, 2026];
  const natByYear = {};
  const cityByYear = {};

  years.forEach(year => {
    natByYear[year] = {};
    cityByYear[year] = {};

    data[year].participants
      .filter(p => p.finishTimeSeconds)
      .forEach(p => {
        if (p.nationality) {
          natByYear[year][p.nationality] = (natByYear[year][p.nationality] || 0) + 1;
        }
        if (p.city) {
          const city = p.city.trim();
          cityByYear[year][city] = (cityByYear[year][city] || 0) + 1;
        }
      });
  });

  // Топ национальностей 2026
  const topNationalities2026 = Object.entries(natByYear[2026])
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([nat, count]) => ({ nationality: nat, count }));

  // Топ городов 2026
  const topCities2026 = Object.entries(cityByYear[2026])
    .sort((a, b) => b[1] - a[1])
    .slice(0, 15)
    .map(([city, count]) => ({ city, count }));

  // Международные участники (не KAZ)
  const internationalByYear = years.map(year => {
    const total = Object.values(natByYear[year]).reduce((a, b) => a + b, 0);
    const kaz = natByYear[year]['KAZ'] || 0;
    return {
      year,
      total,
      international: total - kaz,
      internationalPercent: Math.round((total - kaz) / total * 100)
    };
  });

  return {
    topNationalities2026,
    topCities2026,
    internationalByYear,
    countriesCount2026: Object.keys(natByYear[2026]).length
  };
}

// 6. ВОЗРАСТНОЙ АНАЛИЗ
function analyzeAge(data) {
  const years = [2022, 2023, 2024, 2025, 2026];
  const ageByYear = {};

  years.forEach(year => {
    const currentYear = year;
    const ages = [];
    const ageGroups = {
      'До 18': 0,
      '18-29': 0,
      '30-39': 0,
      '40-49': 0,
      '50-59': 0,
      '60+': 0
    };

    data[year].participants
      .filter(p => p.finishTimeSeconds && p.birthYear)
      .forEach(p => {
        const age = currentYear - p.birthYear;
        ages.push(age);

        if (age < 18) ageGroups['До 18']++;
        else if (age <= 29) ageGroups['18-29']++;
        else if (age <= 39) ageGroups['30-39']++;
        else if (age <= 49) ageGroups['40-49']++;
        else if (age <= 59) ageGroups['50-59']++;
        else ageGroups['60+']++;
      });

    ages.sort((a, b) => a - b);
    ageByYear[year] = {
      youngest: ages[0],
      oldest: ages[ages.length - 1],
      median: ages[Math.floor(ages.length / 2)],
      average: Math.round(ages.reduce((a, b) => a + b, 0) / ages.length),
      groups: ageGroups
    };
  });

  // Самые возрастные финишёры 2026
  const oldestFinishers2026 = data[2026].participants
    .filter(p => p.finishTimeSeconds && p.birthYear)
    .map(p => ({
      name: p.name,
      age: 2026 - p.birthYear,
      distance: p.distance,
      time: secondsToTime(p.finishTimeSeconds)
    }))
    .sort((a, b) => b.age - a.age)
    .slice(0, 5);

  // Самые молодые финишёры 2026
  const youngestFinishers2026 = data[2026].participants
    .filter(p => p.finishTimeSeconds && p.birthYear)
    .map(p => ({
      name: p.name,
      age: 2026 - p.birthYear,
      distance: p.distance,
      time: secondsToTime(p.finishTimeSeconds)
    }))
    .sort((a, b) => a.age - b.age)
    .slice(0, 5);

  return {
    byYear: ageByYear,
    oldestFinishers2026,
    youngestFinishers2026
  };
}

// 7. АНАЛИЗ ПРОГРЕССА УЧАСТНИКОВ
function analyzeProgress(data) {
  const participantsByName = {};
  const years = [2022, 2023, 2024, 2025, 2026];

  // Группируем результаты по VK 1000 (самая популярная дистанция)
  years.forEach(year => {
    data[year].participants
      .filter(p => p.finishTimeSeconds && (p.distance === 'VK 1000' || p.distance === 'Vertical Kilometer 1000'))
      .forEach(p => {
        const name = p.name.toLowerCase().trim();
        if (!participantsByName[name]) {
          participantsByName[name] = {
            name: p.name,
            results: []
          };
        }
        participantsByName[name].results.push({
          year,
          time: p.finishTimeSeconds
        });
      });
  });

  // Находим участников с максимальным улучшением
  const progressStats = Object.values(participantsByName)
    .filter(p => p.results.length >= 2)
    .map(p => {
      const sorted = [...p.results].sort((a, b) => a.year - b.year);
      const first = sorted[0];
      const last = sorted[sorted.length - 1];
      const improvement = first.time - last.time;
      return {
        name: p.name,
        firstYear: first.year,
        lastYear: last.year,
        firstTime: secondsToTime(first.time),
        lastTime: secondsToTime(last.time),
        improvementSeconds: improvement,
        improvementFormatted: secondsToTime(Math.abs(improvement)),
        improved: improvement > 0,
        participations: p.results.length
      };
    })
    .filter(p => p.improved && p.improvementSeconds > 60) // Улучшились хотя бы на минуту
    .sort((a, b) => b.improvementSeconds - a.improvementSeconds)
    .slice(0, 15);

  return {
    topImprovers: progressStats,
    totalWithMultipleRaces: Object.values(participantsByName).filter(p => p.results.length >= 2).length
  };
}

// 8. ГЕНДЕРНЫЙ АНАЛИЗ
function analyzeGender(data) {
  const years = [2022, 2023, 2024, 2025, 2026];

  const genderTrend = years.map(year => {
    const men = data[year].stats.byGender.M;
    const women = data[year].stats.byGender.F;
    return {
      year,
      men,
      women,
      total: men + women,
      womenPercent: Math.round(women / (men + women) * 100)
    };
  });

  // Рост женского участия
  const womenGrowth = Math.round((genderTrend[4].women - genderTrend[0].women) / genderTrend[0].women * 100);

  return {
    trend: genderTrend,
    womenGrowthPercent: womenGrowth,
    womenRecord2026: genderTrend[4].women
  };
}

// 9. АНАЛИЗ ДИСТАНЦИЙ
function analyzeDistances(data) {
  const years = [2022, 2023, 2024, 2025, 2026];
  const distancePopularity = {};

  const distanceMapping = {
    'VK 1000': 'VK 1000',
    'Vertical Kilometer 1000': 'VK 1000',
    'SS 600': 'SS 600',
    'SkySprint 600': 'SS 600',
    'SR 1500': 'SR 1500',
    'SkyRace 1500': 'SR 1500',
    'SR 1400': 'SR 1400'
  };

  years.forEach(year => {
    data[year].participants
      .filter(p => p.finishTimeSeconds && p.distance)
      .forEach(p => {
        const dist = distanceMapping[p.distance] || p.distance;
        if (!dist || dist === 'Unknown') return;

        if (!distancePopularity[dist]) {
          distancePopularity[dist] = {};
        }
        distancePopularity[dist][year] = (distancePopularity[dist][year] || 0) + 1;
      });
  });

  return {
    byDistance: distancePopularity,
    mostPopular2026: Object.entries(distancePopularity)
      .map(([dist, years]) => ({ distance: dist, count: years[2026] || 0 }))
      .sort((a, b) => b.count - a.count)
  };
}

// Главная функция
function main() {
  console.log('📊 Amangeldy Race - Расширенная аналитика\n');
  console.log('='.repeat(50));

  if (!fs.existsSync(OUTPUT_DIR)) {
    fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  }

  const data = loadAllYears();
  console.log('✅ Данные загружены\n');

  // Собираем всю аналитику
  const analytics = {
    generatedAt: new Date().toISOString(),
    eventName: 'ВЫСОКОГОРНЫЙ ЗАБЕГ ИМЕНИ А.БУКРЕЕВА «AMANGELDY RACE»',

    growth: analyzeGrowth(data),
    clubs: analyzeClubs(data),
    veterans: analyzeVeterans(data),
    records: analyzeRecords(data),
    geography: analyzeGeography(data),
    age: analyzeAge(data),
    progress: analyzeProgress(data),
    gender: analyzeGender(data),
    distances: analyzeDistances(data)
  };

  // Сохраняем полную аналитику
  const outputFile = path.join(OUTPUT_DIR, 'full_analytics.json');
  fs.writeFileSync(outputFile, JSON.stringify(analytics, null, 2), 'utf8');
  console.log(`✅ Полная аналитика: ${outputFile}`);

  // Создаём краткие инсайты для соцсетей
  const insights = createSocialInsights(analytics);
  const insightsFile = path.join(OUTPUT_DIR, 'social_insights.json');
  fs.writeFileSync(insightsFile, JSON.stringify(insights, null, 2), 'utf8');
  console.log(`✅ Инсайты для соцсетей: ${insightsFile}`);

  // Выводим ключевые цифры
  printKeyStats(analytics);
}

// Создание инсайтов для соцсетей
function createSocialInsights(a) {
  return {
    headline: `AMANGELDY RACE 2026: Рекорд участия - ${a.growth.summary.recordParticipants2026} человек!`,

    keyNumbers: {
      participants2026: a.growth.summary.recordParticipants2026,
      growthSince2022: `+${a.growth.summary.totalGrowthPercent}%`,
      womenGrowth: `+${a.growth.summary.womenGrowthPercent}%`,
      womenPercent2026: `${a.growth.summary.womenPercentage2026}%`,
      countries2026: a.geography.countriesCount2026,
      uniqueParticipantsAllTime: a.veterans.totalUniqueParticipants,
      fiveYearVeterans: a.veterans.fiveYearVeteransCount,
      totalClubs2026: a.clubs.totalClubs2026
    },

    carouselSlides: [
      {
        title: '🏔️ Рекордный 2026',
        stats: [
          `${a.growth.summary.recordParticipants2026} участников`,
          `Рост на ${a.growth.summary.totalGrowthPercent}% с 2022`,
          `${a.growth.yearByYear[4].finished} финишёров`
        ]
      },
      {
        title: '👩 Женский бег на подъёме',
        stats: [
          `${a.gender.womenRecord2026} женщин в 2026`,
          `Рост на ${a.gender.womenGrowthPercent}% с 2022`,
          `${a.growth.summary.womenPercentage2026}% от всех участников`
        ]
      },
      {
        title: '🌍 География',
        stats: [
          `${a.geography.countriesCount2026} стран`,
          `Топ: ${a.geography.topNationalities2026.slice(0, 3).map(n => n.nationality).join(', ')}`,
          `${a.geography.internationalByYear[4].internationalPercent}% иностранцев`
        ]
      },
      {
        title: '🏃 Топ клубы 2026',
        stats: a.clubs.topClubsAllTime.slice(0, 5).map(c => `${c.name}: ${c.total}`)
      },
      {
        title: '🎖️ Ветераны',
        stats: [
          `${a.veterans.fiveYearVeteransCount} участников всех 5 гонок`,
          `${a.veterans.totalUniqueParticipants} уникальных бегунов за всё время`,
          `${a.veterans.returningPercent2026}% вернулись в 2026`
        ]
      },
      {
        title: '👴👶 Возраст',
        stats: [
          `Самый молодой: ${a.age.youngestFinishers2026[0]?.age} лет`,
          `Самый возрастной: ${a.age.oldestFinishers2026[0]?.age} лет`,
          `Средний возраст: ${a.age.byYear[2026].average} лет`
        ]
      }
    ],

    topClubs2026: a.clubs.topClubsAllTime.slice(0, 10),
    fiveYearVeterans: a.veterans.fiveYearVeterans.slice(0, 20),
    topImprovers: a.progress.topImprovers.slice(0, 10),
    newClubs2026: a.clubs.newClubs2026
  };
}

// Вывод ключевой статистики
function printKeyStats(a) {
  console.log('\n📈 КЛЮЧЕВЫЕ ЦИФРЫ:');
  console.log('─'.repeat(50));
  console.log(`\n🏔️  AMANGELDY RACE 2026`);
  console.log(`   Участников: ${a.growth.summary.recordParticipants2026} (рекорд!)`);
  console.log(`   Рост с 2022: +${a.growth.summary.totalGrowthPercent}%`);
  console.log(`   Женщин: ${a.gender.womenRecord2026} (+${a.gender.womenGrowthPercent}% с 2022)`);
  console.log(`   Стран: ${a.geography.countriesCount2026}`);
  console.log(`   Клубов: ${a.clubs.totalClubs2026}`);

  console.log(`\n🎖️  ВЕТЕРАНЫ (все 5 лет): ${a.veterans.fiveYearVeteransCount} человек`);
  console.log(`   Уникальных за всё время: ${a.veterans.totalUniqueParticipants}`);
  console.log(`   Вернулись в 2026: ${a.veterans.returningPercent2026}%`);

  console.log(`\n🏆 ТОП-5 КЛУБОВ (все годы):`);
  a.clubs.topClubsAllTime.slice(0, 5).forEach((c, i) => {
    console.log(`   ${i + 1}. ${c.name}: ${c.total} финишей`);
  });

  console.log(`\n👴 ВОЗРАСТ 2026:`);
  console.log(`   Самый молодой: ${a.age.youngestFinishers2026[0]?.name} (${a.age.youngestFinishers2026[0]?.age} лет)`);
  console.log(`   Самый возрастной: ${a.age.oldestFinishers2026[0]?.name} (${a.age.oldestFinishers2026[0]?.age} лет)`);

  console.log('\n✨ Аналитика завершена!');
}

main();
