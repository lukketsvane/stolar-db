/**
 * create_chair_json.mjs — Create individual JSON files for each chair
 * in its folder alongside the GLB model and image.
 */
import { readFileSync, writeFileSync, readdirSync, existsSync } from 'fs';
import { join, resolve } from 'path';

const noreg = resolve(import.meta.dirname);
const data = JSON.parse(readFileSync(join(noreg, 'nasjonalmuseet_stoler_128.json'), 'utf-8'));

let created = 0;
let skipped = 0;

for (const chair of data) {
  const id = chair.objectId;
  const folder = join(noreg, id);

  if (!existsSync(folder)) {
    console.log(`  SKIP  ${id} — no folder`);
    skipped++;
    continue;
  }

  const outPath = join(folder, `${id}.json`);
  writeFileSync(outPath, JSON.stringify(chair, null, 2), 'utf-8');
  console.log(`  OK    ${id}`);
  created++;
}

console.log(`\nDone: ${created} created, ${skipped} skipped`);
