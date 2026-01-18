/**
 * Парсер данных Amangeldy Race с live.myrace.info
 * Загружает XML данные и конвертирует в JSON
 */

const https = require('https');
const http = require('http');
const fs = require('fs');
const path = require('path');

const URLS = {
  2026: 'https://live.myrace.info/bases/kz/2026/amangeldyrace2026/amrace2026.clax',
  2025: 'https://live.myrace.info/bases/kz/2025/amangeldy2025/amrace2025.clax',
  2024: 'https://live.myrace.info/bases/kz/2024/amangeldyrace2024/amrace2024.clax',
  2023: 'https://live.myrace.info/bases/kz/2023/amangeldyrace2023/amangeldy2023.clax',
  2022: 'https://live.myrace.info/bases/kz/2022/AR2022/AmangeldyRace2022.clax'
};

const DATA_DIR = path.join(__dirname, '..', 'data');

// Функция загрузки URL
function fetchUrl(url) {
  return new Promise((resolve, reject) => {
    const protocol = url.startsWith('https') ? https : http;
    protocol.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve(data));
    }).on('error', reject);
  });
}

// Парсинг XML атрибутов из строки тега
function parseAttributes(tagContent) {
  const attrs = {};
  const regex = /(\w+)="([^"]*)"/g;
  let match;
  while ((match = regex.exec(tagContent)) !== null) {
    attrs[match[1]] = match[2];
  }
  return attrs;
}

// Извлечение всех тегов определённого типа
function extractTags(xml, tagName) {
  const results = [];
  const regex = new RegExp(`<${tagName}\\s+([^>]*?)\\s*/>`, 'g');
  let match;
  while ((match = regex.exec(xml)) !== null) {
    results.push(parseAttributes(match[1]));
  }
  return results;
}

// Извлечение информации о событии
function extractEventInfo(xml) {
  const info = {};

  // Название
  const nomMatch = xml.match(/nom="([^"]*)"/);
  if (nomMatch) info.name = nomMatch[1];

  // Организатор
  const orgMatch = xml.match(/organisateur="([^"]*)"/);
  if (orgMatch) info.organizer = orgMatch[1];

  // Дата
  const dateMatch = xml.match(/dates="([^"]*)"/);
  if (dateMatch) info.date = dateMatch[1];

  // Место
  const lieuMatch = xml.match(/lieu="([^"]*)"/);
  if (lieuMatch) info.location = lieuMatch[1];

  return info;
}

// Извлечение информации об этапах/дистанциях
function extractStages(xml) {
  const stages = [];
  const stageRegex = /<Etape\s+([^>]*?)>/g;
  let match;
  while ((match = stageRegex.exec(xml)) !== null) {
    const attrs = parseAttributes(match[1]);
    stages.push({
      id: attrs.num,
      name: attrs.nom || attrs.nom2,
      distance: attrs.distance ? parseInt(attrs.distance) : null,
      elevation: attrs.denivele ? parseInt(attrs.denivele) : null
    });
  }
  return stages;
}

// Конвертация времени в секунды
function timeToSeconds(timeStr) {
  if (!timeStr) return null;

  // Формат: 00h34'06 или 01:23:45
  const hmsMatch = timeStr.match(/(\d+)h(\d+)'(\d+)/);
  if (hmsMatch) {
    return parseInt(hmsMatch[1]) * 3600 + parseInt(hmsMatch[2]) * 60 + parseInt(hmsMatch[3]);
  }

  const colonMatch = timeStr.match(/(\d+):(\d+):(\d+)/);
  if (colonMatch) {
    return parseInt(colonMatch[1]) * 3600 + parseInt(colonMatch[2]) * 60 + parseInt(colonMatch[3]);
  }

  // Формат: 34:06 (минуты:секунды)
  const msMatch = timeStr.match(/^(\d+):(\d+)$/);
  if (msMatch) {
    return parseInt(msMatch[1]) * 60 + parseInt(msMatch[2]);
  }

  return null;
}

// Форматирование секунд обратно во время
function secondsToTime(seconds) {
  if (seconds === null) return null;
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
}

// Основная функция парсинга
async function parseYear(year) {
  console.log(`\n📥 Загружаю данные за ${year}...`);

  const url = URLS[year];
  const xml = await fetchUrl(url);

  console.log(`  Получено ${xml.length} байт`);

  // Извлекаем данные
  const eventInfo = extractEventInfo(xml);
  const stages = extractStages(xml);
  const participants = extractTags(xml, 'E');
  const results = extractTags(xml, 'R');

  console.log(`  Участников: ${participants.length}`);
  console.log(`  Результатов: ${results.length}`);

  // Создаём карту результатов по номеру
  const resultsMap = {};
  results.forEach(r => {
    resultsMap[r.d] = r;
  });

  // Объединяем участников с результатами
  const mergedData = participants.map(p => {
    const result = resultsMap[p.d] || {};
    const timeSeconds = timeToSeconds(result.t);

    return {
      bib: p.d,                          // Номер
      name: p.n,                         // Имя
      club: p.c || null,                 // Клуб
      birthYear: p.a ? parseInt(p.a) : null, // Год рождения
      gender: p.x || null,               // Пол
      category: p.ca || null,            // Категория
      distance: p.p || null,             // Дистанция
      nationality: p.na || null,         // Национальность
      city: p.ip0 || null,               // Город
      didNotStart: p.np === '1',         // Не стартовал
      finishTime: result.t || null,      // Время финиша (строка)
      finishTimeSeconds: timeSeconds,    // Время финиша (секунды)
      pace: result.m || null,            // Темп
      gap: result.g || null              // Отставание
    };
  });

  // Фильтруем финишёров
  const finishers = mergedData.filter(p => p.finishTimeSeconds !== null && !p.didNotStart);

  // Собираем статистику
  const stats = {
    totalRegistered: participants.length,
    totalFinished: finishers.length,
    totalDNS: mergedData.filter(p => p.didNotStart).length,
    byGender: {
      M: finishers.filter(p => p.gender === 'M').length,
      F: finishers.filter(p => p.gender === 'F').length
    },
    byDistance: {},
    byNationality: {},
    byClub: {},
    byCity: {}
  };

  // Статистика по дистанциям
  finishers.forEach(p => {
    const dist = p.distance || 'Unknown';
    if (!stats.byDistance[dist]) {
      stats.byDistance[dist] = { total: 0, M: 0, F: 0, times: [] };
    }
    stats.byDistance[dist].total++;
    if (p.gender) stats.byDistance[dist][p.gender]++;
    if (p.finishTimeSeconds) stats.byDistance[dist].times.push(p.finishTimeSeconds);
  });

  // Считаем средние/медианные времена по дистанциям
  Object.keys(stats.byDistance).forEach(dist => {
    const times = stats.byDistance[dist].times.sort((a, b) => a - b);
    if (times.length > 0) {
      stats.byDistance[dist].fastestTime = secondsToTime(times[0]);
      stats.byDistance[dist].medianTime = secondsToTime(times[Math.floor(times.length / 2)]);
      stats.byDistance[dist].avgTime = secondsToTime(Math.round(times.reduce((a, b) => a + b, 0) / times.length));
    }
    delete stats.byDistance[dist].times; // Удаляем сырые данные
  });

  // Статистика по национальностям
  finishers.forEach(p => {
    const nat = p.nationality || 'Unknown';
    stats.byNationality[nat] = (stats.byNationality[nat] || 0) + 1;
  });

  // Топ клубов
  finishers.forEach(p => {
    if (p.club) {
      stats.byClub[p.club] = (stats.byClub[p.club] || 0) + 1;
    }
  });

  // Топ городов
  finishers.forEach(p => {
    if (p.city) {
      stats.byCity[p.city] = (stats.byCity[p.city] || 0) + 1;
    }
  });

  return {
    year,
    eventInfo,
    stages,
    stats,
    participants: mergedData
  };
}

// Главная функция
async function main() {
  console.log('🏔️  Amangeldy Race Data Parser');
  console.log('================================\n');

  // Создаём директорию если нет
  if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
  }

  const allYearsData = {};
  const allYearsSummary = [];

  for (const year of [2022, 2023, 2024, 2025, 2026]) {
    try {
      const data = await parseYear(year);
      allYearsData[year] = data;

      // Сохраняем данные года
      const yearFile = path.join(DATA_DIR, `${year}.json`);
      fs.writeFileSync(yearFile, JSON.stringify(data, null, 2), 'utf8');
      console.log(`  ✅ Сохранено: ${yearFile}`);

      // Добавляем в сводку
      allYearsSummary.push({
        year,
        date: data.eventInfo.date,
        registered: data.stats.totalRegistered,
        finished: data.stats.totalFinished,
        dns: data.stats.totalDNS,
        men: data.stats.byGender.M,
        women: data.stats.byGender.F,
        distances: Object.keys(data.stats.byDistance)
      });

    } catch (err) {
      console.error(`  ❌ Ошибка для ${year}:`, err.message);
    }
  }

  // Сохраняем сводную информацию
  const summaryFile = path.join(DATA_DIR, 'summary.json');
  fs.writeFileSync(summaryFile, JSON.stringify(allYearsSummary, null, 2), 'utf8');
  console.log(`\n✅ Сводка сохранена: ${summaryFile}`);

  // Собираем объединённую статистику для анализа трендов
  const trends = {
    participation: allYearsSummary.map(y => ({
      year: y.year,
      registered: y.registered,
      finished: y.finished,
      finishRate: Math.round(y.finished / y.registered * 100)
    })),
    genderRatio: allYearsSummary.map(y => ({
      year: y.year,
      men: y.men,
      women: y.women,
      womenPercent: Math.round(y.women / (y.men + y.women) * 100)
    }))
  };

  const trendsFile = path.join(DATA_DIR, 'trends.json');
  fs.writeFileSync(trendsFile, JSON.stringify(trends, null, 2), 'utf8');
  console.log(`✅ Тренды сохранены: ${trendsFile}`);

  // Выводим краткую статистику
  console.log('\n📊 КРАТКАЯ СТАТИСТИКА:');
  console.log('─'.repeat(50));
  allYearsSummary.forEach(y => {
    console.log(`${y.year}: ${y.finished}/${y.registered} финишировали (${Math.round(y.finished/y.registered*100)}%), М:${y.men} Ж:${y.women}`);
  });

  console.log('\n✨ Парсинг завершён!');
}

main().catch(console.error);
