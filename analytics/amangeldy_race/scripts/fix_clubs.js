const fs = require('fs');
const path = require('path');

const dataFile = path.join(__dirname, '..', 'data', '2026.json');
const data = JSON.parse(fs.readFileSync(dataFile, 'utf8'));

// Обновляем клуб для Baikashev Shyngys и Janzakov Niyaz
let updated = 0;
data.participants.forEach(p => {
  if (p.name && (p.name.includes('Baikashev') || p.name.includes('Janzakov'))) {
    console.log('Found:', p.name, 'club:', p.club);
    if (p.club === null) {
      p.club = 'SkyRunGroup';
      updated++;
      console.log('Updated:', p.name, p.distance);
    }
  }
});

console.log('Total updated:', updated);

fs.writeFileSync(dataFile, JSON.stringify(data, null, 2), 'utf8');
console.log('File saved');
