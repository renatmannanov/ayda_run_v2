/**
 * Генерация MD файла из JSON аналитики
 */

const fs = require('fs');
const path = require('path');

const INPUT = path.join(__dirname, '..', 'output', 'participants_clubs_analytics.json');
const OUTPUT = path.join(__dirname, '..', 'output', 'participants_clubs_analytics.md');

const data = JSON.parse(fs.readFileSync(INPUT, 'utf8'));
const p = data.participants;
const c = data.clubs;

let md = `# Amangeldy Race: Аналитика участников и клубов (2022-2026)

> Высокогорный забег имени А. Букреева, Алматы, Казахстан

---

## УЧАСТНИКИ

### 1. Рекорд 2026

**${p.record2026} участников** - абсолютный рекорд за всю историю гонки!

### 2. Динамика роста участников за 5 лет

| Год | Зарегистрировано | Финишировали | Доля финиша |
|-----|------------------|--------------|-------------|
`;

p.participantsDynamics.forEach(d => {
  md += `| ${d.year} | ${d.registered} | ${d.finished} | ${d.finishRate}% |\n`;
});

md += `
**Общий рост:** ${p.totalGrowth.from} → ${p.totalGrowth.to} (**+${p.totalGrowth.growthPercent}%** за 5 лет)

#### Рост по годам:
| Период | Прирост | % роста |
|--------|---------|---------|
`;

p.growthYoY.forEach(g => {
  md += `| ${g.period} | +${g.growth} | +${g.growthPercent}% |\n`;
});

md += `
---

### 3. Женщины - абсолютные числа

| Год | Женщин (финиш) |
|-----|----------------|
`;

p.womenDynamics.forEach(d => {
  md += `| ${d.year} | ${d.women} |\n`;
});

md += `
**Общий рост:** ${p.womenTotalGrowth.from} → ${p.womenTotalGrowth.to} (**+${p.womenTotalGrowth.growthPercent}%** за 5 лет)

#### Рост по годам:
| Период | Прирост | % роста |
|--------|---------|---------|
`;

p.womenGrowthYoY.forEach(g => {
  md += `| ${g.period} | +${g.growth} | +${g.growthPercent}% |\n`;
});

md += `
---

### 4. Женщины - доля от общего количества

| Год | Женщин | Всего финишёров | Доля женщин |
|-----|--------|-----------------|-------------|
`;

p.womenDynamics.forEach(d => {
  md += `| ${d.year} | ${d.women} | ${d.total} | ${d.womenPercent}% |\n`;
});

md += `
**Рост доли:** ${p.womenTotalGrowth.shareFrom}% → ${p.womenTotalGrowth.shareTo}% (**+${(p.womenTotalGrowth.shareTo - p.womenTotalGrowth.shareFrom).toFixed(1)} п.п.** за 5 лет)

---

### 5. Ветераны - участники 4-5 гонок

**Всего ветеранов:** ${p.veterans.fourPlusTotal} человек
- 5 гонок: ${p.veterans.fiveRacesCount} человек
- 4 гонки: ${p.veterans.fourRacesCount} человек

#### Ветераны всех 5 гонок (2022-2026):

| Имя | Клуб |
|-----|------|
`;

p.veterans.fiveRaces.forEach(v => {
  md += `| ${v.name} | ${v.club || '—'} |\n`;
});

md += `
---

### 6. Новички и вернувшиеся участники

| Год | Новички | % | Вернулись | % | Всего |
|-----|---------|---|-----------|---|-------|
`;

p.newcomersByYear.forEach(d => {
  md += `| ${d.year} | ${d.newcomers} | ${d.newcomersPercent}% | ${d.returning} | ${d.returningPercent}% | ${d.total} |\n`;
});

md += `
> В 2022 году все участники считаются новичками (первый год гонки)

---

## КЛУБЫ

### 1. Количество клубов в 2026

**${c.clubs2026Count} клубов** представлены на гонке 2026

### 2. Уникальных клубов за всё время

**${c.uniqueClubsTotal} клубов** участвовали хотя бы в одной гонке за 5 лет

### 3. Динамика роста количества клубов

| Год | Количество клубов |
|-----|-------------------|
`;

c.clubsDynamics.forEach(d => {
  md += `| ${d.year} | ${d.clubsCount} |\n`;
});

md += `
> Примечание: резкий рост в 2024 связан с улучшением сбора данных о клубах

#### Рост по годам:
| Период | Прирост | % роста |
|--------|---------|---------|
`;

c.clubsGrowthYoY.forEach(g => {
  md += `| ${g.period} | +${g.growth} | +${g.growthPercent}% |\n`;
});

md += `
---

### 4. Топ-10 клубов по годам (уникальные участники)

`;

['2022', '2023', '2024', '2025', '2026'].forEach(year => {
  md += `#### ${year}
| # | Клуб | Участников | М | Ж | % жен |
|---|------|------------|---|---|-------|
`;
  c.top10ByYear[year].forEach((club, i) => {
    md += `| ${i + 1} | ${club.club} | ${club.total} | ${club.men} | ${club.women} | ${club.womenPercent}% |\n`;
  });
  md += '\n';
});

md += `---

### 5. Рост участников в топ-10 клубах 2026 за 5 лет

| Клуб | 2022 | 2023 | 2024 | 2025 | 2026 | Рост (с первого года) |
|------|------|------|------|------|------|----------------------|
`;

c.top10ClubsGrowth.forEach(club => {
  const h = club.history;
  const vals = h.map(y => y.total === 0 ? '—' : y.total).join(' | ');
  const growthStr = club.growthPercent !== null ? `${club.growthPercent > 0 ? '+' : ''}${club.growthPercent}%` : '—';
  md += `| ${club.club} | ${vals} | ${growthStr} |\n`;
});

md += `
---

### 6. Доля женщин в топ-10 клубах 2026 за 5 лет

| Клуб | 2022 | 2023 | 2024 | 2025 | 2026 | Изменение доли |
|------|------|------|------|------|------|----------------|
`;

c.top10ClubsWomenGrowth.forEach(club => {
  const h = club.history;
  const vals = h.map(y => y.womenPercent === null ? '—' : y.womenPercent + '%').join(' | ');
  const changeStr = club.womenShareGrowth !== null ? `${club.womenShareGrowth > 0 ? '+' : ''}${club.womenShareGrowth} п.п.` : '—';
  md += `| ${club.club} | ${vals} | ${changeStr} |\n`;
});

md += `
---

## ДИСТАНЦИИ

### 1. Участники по дистанциям

`;

const d = data.distances;
d.distancesByYear.forEach(({ year, distances }) => {
  md += `#### ${year}
| Дистанция | Участников | М | Ж | % жен | Клубов |
|-----------|------------|---|---|-------|--------|
`;
  distances.forEach(dist => {
    md += `| ${dist.distance} | ${dist.total} | ${dist.men} | ${dist.women} | ${dist.womenPercent}% | ${dist.clubsCount} |\n`;
  });
  md += '\n';
});

md += `---

### 2. Динамика роста по дистанциям

| Дистанция | 2022 | 2023 | 2024 | 2025 | 2026 | Рост |
|-----------|------|------|------|------|------|------|
`;

Object.entries(d.distanceGrowth).forEach(([distance, dData]) => {
  const vals = dData.history.map(h => h.total === 0 ? '—' : h.total).join(' | ');
  const growthStr = dData.growthPercent !== null ? `${dData.growthPercent > 0 ? '+' : ''}${dData.growthPercent}%` : '—';
  md += `| ${distance} | ${vals} | ${growthStr} |\n`;
});

md += `
---

## Ключевые выводы

### Участники
- Рекордный 2026: **${p.record2026} участников** (+${p.totalGrowth.growthPercent}% за 5 лет)
- Женский бег растёт быстрее: **+${p.womenTotalGrowth.growthPercent}%** (vs +${p.totalGrowth.growthPercent}% общий рост)
- Доля женщин выросла с ${p.womenTotalGrowth.shareFrom}% до **${p.womenTotalGrowth.shareTo}%**
- **${p.veterans.fiveRacesCount} ветеранов** прошли все 5 гонок
- **${p.newcomersByYear[4].returningPercent}%** участников 2026 уже бежали раньше

### Клубы
- **${c.clubs2026Count} клубов** в 2026 году
- **${c.uniqueClubsTotal} уникальных клубов** за всю историю
- Лидер 2026: **${c.top10ByYear['2026'][0].club}** (${c.top10ByYear['2026'][0].total} участников)

### Дистанции
- Самая популярная: **${d.distancesByYear[4].distances[0].distance}** (${d.distancesByYear[4].distances[0].total} участников)
- Самая женская: **${d.distancesByYear[4].distances.reduce((a, b) => a.womenPercent > b.womenPercent ? a : b).distance}** (${d.distancesByYear[4].distances.reduce((a, b) => a.womenPercent > b.womenPercent ? a : b).womenPercent}% женщин)

---

*Данные собраны с live.myrace.info*
*Дата генерации: ${new Date().toLocaleDateString('ru-RU')}*
`;

fs.writeFileSync(OUTPUT, md, 'utf8');
console.log('MD файл сгенерирован:', OUTPUT);
