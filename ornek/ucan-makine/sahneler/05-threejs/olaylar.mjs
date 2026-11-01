// olaylar.json: ses icin olay listesi, zaman.js'teki ayni krank acisindan (goruntudeki anla ayni kare)
import {writeFileSync} from 'node:fs';
import {olaylar, TUR} from './zaman.js';
const o = olaylar();
writeFileSync(new URL('./olaylar.json', import.meta.url), JSON.stringify(o, null, 1) + '\n');
console.log(`olaylar.json: ${o.length} olay, ${TUR} kanat turu`);
