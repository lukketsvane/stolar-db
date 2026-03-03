import { createRequire } from 'module';
const require = createRequire(import.meta.url);
const { ChartJSNodeCanvas } = require('chartjs-node-canvas');
import fs from 'fs';
import path from 'path';

const BASE_DIR = 'C:/Users/Shadow/Desktop/stolar-db/noreg';
const CHARTS_DIR = path.join(BASE_DIR, 'charts');
const MASTER_JSON = path.join(BASE_DIR, 'nasjonalmuseet_stoler_128.json');
const WEIGHTS_JSON = path.join(BASE_DIR, 'weight_estimates.json');

if (!fs.existsSync(CHARTS_DIR)) fs.mkdirSync(CHARTS_DIR, { recursive: true });

const WIDTH = 1200;
const HEIGHT = 700;
const chartJSNodeCanvas = new ChartJSNodeCanvas({ width: WIDTH, height: HEIGHT, backgroundColour: '#ffffff' });

// Color palette
const COLORS = {
  primary: '#2563eb',
  secondary: '#dc2626',
  accent: '#059669',
  wood: '#8B6914',
  metal: '#6B7280',
  plastic: '#7C3AED',
  textile: '#EC4899',
  bg: '#f8fafc',
};

const MATERIAL_COLORS = {
  'Eik': '#8B4513', 'Mahogni': '#6B3A2A', 'Bøk': '#C4A35A', 'Ask': '#D2B48C',
  'Bjørk': '#F5DEB3', 'Furu': '#DEB887', 'Gran': '#90EE90', 'Tre': '#A0522D',
  'Kryssfiner': '#D2691E', 'Alm': '#CD853F', 'Or': '#DAA520',
  'Stål': '#708090', 'Stålrør': '#A9A9A9', 'Jern': '#696969', 'Metall': '#778899',
  'Plast': '#9370DB', 'Polyuretan': '#BA55D3', 'Polyamid': '#DDA0DD',
};

function parseYear(datering) {
  if (!datering) return null;
  // "1632" → 1632
  const exact = datering.match(/^(\d{4})$/);
  if (exact) return parseInt(exact[1]);
  // "Slutten av 1600-tallet" → 1690
  const slutten = datering.match(/[Ss]lutten av (\d{4})-tallet/);
  if (slutten) return parseInt(slutten[1]) + 90;
  // "Begynnelsen av 1800-tallet" → 1810
  const begynnelsen = datering.match(/[Bb]egynnelsen av (\d{4})-tallet/);
  if (begynnelsen) return parseInt(begynnelsen[1]) + 10;
  // "Midten av 1800-tallet" → 1850
  const midten = datering.match(/[Mm]idten av (\d{4})-tallet/);
  if (midten) return parseInt(midten[1]) + 50;
  // "1700-tallet" → 1750
  const tallet = datering.match(/(\d{4})-tallet/);
  if (tallet) return parseInt(tallet[1]) + 50;
  // "ca. 1750" → 1750
  const ca = datering.match(/ca\.?\s*(\d{4})/);
  if (ca) return parseInt(ca[1]);
  // "1750–1760" → 1755
  const range = datering.match(/(\d{4})\s*[–-]\s*(\d{4})/);
  if (range) return Math.round((parseInt(range[1]) + parseInt(range[2])) / 2);
  // "Etter 1800" → 1810
  const etter = datering.match(/[Ee]tter\s*(\d{4})/);
  if (etter) return parseInt(etter[1]) + 10;
  // "Før 1800" → 1790
  const foer = datering.match(/[Ff]ør\s*(\d{4})/);
  if (foer) return parseInt(foer[1]) - 10;
  // Extract any 4-digit year
  const any4 = datering.match(/(\d{4})/);
  if (any4) return parseInt(any4[1]);
  return null;
}

function getMaterialGroup(mat) {
  const woods = ['Eik', 'Mahogni', 'Bøk', 'Ask', 'Bjørk', 'Furu', 'Gran', 'Tre', 'Kryssfiner', 'Alm', 'Or', 'Jakaranda', 'Buksbom', 'Palme', 'Whitewood'];
  const metals = ['Stål', 'Stålrør', 'Jern', 'Messing', 'Bronse', 'Metall'];
  const plastics = ['Plast', 'Gummi', 'Gummi/plast', 'Polyuretan', 'Polyamid', 'Skumplast'];
  if (woods.includes(mat)) return 'Tre';
  if (metals.includes(mat)) return 'Metall';
  if (plastics.includes(mat)) return 'Plast';
  return 'Anna';
}

async function renderChart(config, filename) {
  const buffer = await chartJSNodeCanvas.renderToBuffer(config);
  const outPath = path.join(CHARTS_DIR, filename);
  fs.writeFileSync(outPath, buffer);
  console.log(`  → ${filename} (${(buffer.length / 1024).toFixed(0)} KB)`);
}

async function main() {
  const masterData = JSON.parse(fs.readFileSync(MASTER_JSON, 'utf8'));
  const weightData = JSON.parse(fs.readFileSync(WEIGHTS_JSON, 'utf8'));

  // Merge data
  const chairs = weightData.chairs
    .filter(c => c.estimatedWeight_kg && !c.error)
    .map(c => {
      const master = masterData.find(m => m.objectId === c.objectId);
      return {
        ...c,
        year: parseYear(c.datering),
        materialGroup: getMaterialGroup(c.primaryMaterial),
        master,
      };
    })
    .filter(c => c.year); // only chairs with parseable dates

  console.log(`${chairs.length} chairs with weight + year data\n`);

  // ===== CHART 1: Scatter — Weight × Year, colored by material group =====
  console.log('Chart 1: Weight × Year scatter...');
  const groups = ['Tre', 'Metall', 'Plast', 'Anna'];
  const groupColors = { 'Tre': COLORS.wood, 'Metall': COLORS.metal, 'Plast': COLORS.plastic, 'Anna': COLORS.textile };

  await renderChart({
    type: 'scatter',
    data: {
      datasets: groups.map(g => ({
        label: g,
        data: chairs.filter(c => c.materialGroup === g).map(c => ({ x: c.year, y: c.estimatedWeight_kg })),
        backgroundColor: groupColors[g] + '99',
        borderColor: groupColors[g],
        pointRadius: 6,
        pointHoverRadius: 9,
      })),
    },
    options: {
      plugins: {
        title: { display: true, text: 'Estimert vekt over tid (n='+chairs.length+')', font: { size: 18 } },
        legend: { position: 'top' },
      },
      scales: {
        x: { title: { display: true, text: 'Årstal' }, min: 1250, max: 2030 },
        y: { title: { display: true, text: 'Estimert vekt (kg)' }, min: 0 },
      },
    },
  }, '01_weight_over_time.png');

  // ===== CHART 2: Bar — Material distribution per century =====
  console.log('Chart 2: Material distribution per century...');
  const centuries = [1300, 1400, 1500, 1600, 1700, 1800, 1900, 2000];
  const centuryLabels = centuries.map(c => `${c}-talet`);
  const matGroupCounts = {};
  for (const g of groups) matGroupCounts[g] = centuries.map(() => 0);
  for (const c of chairs) {
    const cenIdx = centuries.findIndex((cent, i) => c.year >= cent && (i === centuries.length - 1 || c.year < centuries[i + 1]));
    if (cenIdx >= 0) matGroupCounts[c.materialGroup][cenIdx]++;
  }

  await renderChart({
    type: 'bar',
    data: {
      labels: centuryLabels,
      datasets: groups.map(g => ({
        label: g,
        data: matGroupCounts[g],
        backgroundColor: groupColors[g] + 'CC',
        borderColor: groupColors[g],
        borderWidth: 1,
      })),
    },
    options: {
      plugins: {
        title: { display: true, text: 'Materialfordeling per hundreår', font: { size: 18 } },
        legend: { position: 'top' },
      },
      scales: {
        x: { stacked: true, title: { display: true, text: 'Hundreår' } },
        y: { stacked: true, title: { display: true, text: 'Antal stolar' } },
      },
    },
  }, '02_material_per_century.png');

  // ===== CHART 3: Line — Average weight per 50-year period =====
  console.log('Chart 3: Average weight per period...');
  const periods = [];
  for (let y = 1600; y <= 2000; y += 50) periods.push(y);
  const periodLabels = periods.map(p => `${p}–${p + 49}`);
  const periodWeights = periods.map(p => {
    const inPeriod = chairs.filter(c => c.year >= p && c.year < p + 50);
    if (inPeriod.length === 0) return null;
    return +(inPeriod.reduce((s, c) => s + c.estimatedWeight_kg, 0) / inPeriod.length).toFixed(1);
  });
  const periodCounts = periods.map(p => chairs.filter(c => c.year >= p && c.year < p + 50).length);

  await renderChart({
    type: 'line',
    data: {
      labels: periodLabels,
      datasets: [
        {
          label: 'Gjennomsnittleg vekt (kg)',
          data: periodWeights,
          borderColor: COLORS.primary,
          backgroundColor: COLORS.primary + '33',
          fill: true,
          tension: 0.3,
          pointRadius: 5,
          yAxisID: 'y',
        },
        {
          label: 'Antal stolar',
          data: periodCounts,
          borderColor: COLORS.secondary,
          backgroundColor: COLORS.secondary + '33',
          borderDash: [5, 5],
          tension: 0.3,
          pointRadius: 4,
          yAxisID: 'y1',
        },
      ],
    },
    options: {
      plugins: {
        title: { display: true, text: 'Gjennomsnittleg estimert vekt per 50-årsperiode', font: { size: 18 } },
      },
      scales: {
        y: { type: 'linear', position: 'left', title: { display: true, text: 'Vekt (kg)' }, min: 0 },
        y1: { type: 'linear', position: 'right', title: { display: true, text: 'Antal' }, min: 0, grid: { drawOnChartArea: false } },
      },
    },
  }, '03_avg_weight_per_period.png');

  // ===== CHART 4: Box-style — Dimensions per style period =====
  console.log('Chart 4: Dimensions per style period...');
  const stilperioder = {};
  chairs.forEach(c => {
    const sp = c.stilperiode || 'Ukjent';
    if (!stilperioder[sp]) stilperioder[sp] = [];
    stilperioder[sp].push(c);
  });
  // Sort by earliest year
  const spSorted = Object.entries(stilperioder)
    .map(([sp, cs]) => ({ sp, chairs: cs, avgYear: cs.reduce((s, c) => s + c.year, 0) / cs.length }))
    .sort((a, b) => a.avgYear - b.avgYear)
    .filter(s => s.chairs.length >= 2); // at least 2 chairs

  const spLabels = spSorted.map(s => `${s.sp} (n=${s.chairs.length})`);
  const avgH = spSorted.map(s => +(s.chairs.reduce((sum, c) => sum + (c.dimensions?.H || 0), 0) / s.chairs.length).toFixed(1));
  const avgB = spSorted.map(s => +(s.chairs.reduce((sum, c) => sum + (c.dimensions?.B || 0), 0) / s.chairs.length).toFixed(1));
  const avgD = spSorted.map(s => +(s.chairs.reduce((sum, c) => sum + (c.dimensions?.D || 0), 0) / s.chairs.length).toFixed(1));

  await renderChart({
    type: 'bar',
    data: {
      labels: spLabels,
      datasets: [
        { label: 'Høgde (cm)', data: avgH, backgroundColor: '#2563eb99', borderColor: '#2563eb', borderWidth: 1 },
        { label: 'Breidde (cm)', data: avgB, backgroundColor: '#059669aa', borderColor: '#059669', borderWidth: 1 },
        { label: 'Djupne (cm)', data: avgD, backgroundColor: '#dc262699', borderColor: '#dc2626', borderWidth: 1 },
      ],
    },
    options: {
      plugins: {
        title: { display: true, text: 'Gjennomsnittlege dimensjonar per stilperiode', font: { size: 18 } },
      },
      scales: {
        y: { title: { display: true, text: 'cm' }, min: 0 },
      },
    },
  }, '04_dimensions_per_style.png');

  // ===== CHART 5: Weight per material group (grouped bar) =====
  console.log('Chart 5: Weight per material...');
  const topMaterials = {};
  chairs.forEach(c => {
    const m = c.primaryMaterial;
    if (!topMaterials[m]) topMaterials[m] = [];
    topMaterials[m].push(c.estimatedWeight_kg);
  });
  const matSorted = Object.entries(topMaterials)
    .map(([mat, ws]) => ({ mat, avg: ws.reduce((s, w) => s + w, 0) / ws.length, count: ws.length, min: Math.min(...ws), max: Math.max(...ws) }))
    .filter(m => m.count >= 2)
    .sort((a, b) => b.avg - a.avg);

  await renderChart({
    type: 'bar',
    data: {
      labels: matSorted.map(m => `${m.mat} (n=${m.count})`),
      datasets: [
        {
          label: 'Gjennomsnittleg vekt (kg)',
          data: matSorted.map(m => +m.avg.toFixed(1)),
          backgroundColor: matSorted.map(m => (MATERIAL_COLORS[m.mat] || '#888888') + 'CC'),
          borderColor: matSorted.map(m => MATERIAL_COLORS[m.mat] || '#888888'),
          borderWidth: 1,
        },
      ],
    },
    options: {
      indexAxis: 'y',
      plugins: {
        title: { display: true, text: 'Gjennomsnittleg estimert vekt per materiale', font: { size: 18 } },
        legend: { display: false },
      },
      scales: {
        x: { title: { display: true, text: 'Vekt (kg)' }, min: 0 },
      },
    },
  }, '05_weight_per_material.png');

  // ===== CHART 6: Pie — Material group distribution =====
  console.log('Chart 6: Material group pie...');
  const groupCounts = {};
  chairs.forEach(c => {
    groupCounts[c.materialGroup] = (groupCounts[c.materialGroup] || 0) + 1;
  });

  await renderChart({
    type: 'doughnut',
    data: {
      labels: Object.keys(groupCounts),
      datasets: [{
        data: Object.values(groupCounts),
        backgroundColor: Object.keys(groupCounts).map(g => groupColors[g] || '#888'),
        borderWidth: 2,
      }],
    },
    options: {
      plugins: {
        title: { display: true, text: 'Materialgrupper i 3D-skanna stolar (n='+chairs.length+')', font: { size: 18 } },
        legend: { position: 'right' },
      },
    },
  }, '06_material_groups_pie.png');

  // ===== CHART 7: Histogram — Weight distribution =====
  console.log('Chart 7: Weight histogram...');
  const bins = [0, 5, 10, 15, 20, 25, 30, 40, 50, 80];
  const binLabels = bins.slice(0, -1).map((b, i) => `${b}–${bins[i + 1]} kg`);
  const binCounts = bins.slice(0, -1).map((b, i) =>
    chairs.filter(c => c.estimatedWeight_kg >= b && c.estimatedWeight_kg < bins[i + 1]).length
  );

  await renderChart({
    type: 'bar',
    data: {
      labels: binLabels,
      datasets: [{
        label: 'Antal stolar',
        data: binCounts,
        backgroundColor: COLORS.primary + 'CC',
        borderColor: COLORS.primary,
        borderWidth: 1,
      }],
    },
    options: {
      plugins: {
        title: { display: true, text: 'Fordeling av estimert vekt', font: { size: 18 } },
        legend: { display: false },
      },
      scales: {
        x: { title: { display: true, text: 'Vektklasse' } },
        y: { title: { display: true, text: 'Antal stolar' }, min: 0 },
      },
    },
  }, '07_weight_histogram.png');

  // ===== Print summary statistics =====
  console.log('\n=== ANALYSESAMANDRAG ===');
  console.log(`Stolar med vektestimat og årstal: ${chairs.length}`);
  console.log(`Tidsspenn: ${Math.min(...chairs.map(c => c.year))} – ${Math.max(...chairs.map(c => c.year))}`);
  console.log(`\nVekt:`);
  const ws = chairs.map(c => c.estimatedWeight_kg).sort((a, b) => a - b);
  console.log(`  Min: ${ws[0]} kg`);
  console.log(`  Max: ${ws[ws.length - 1]} kg`);
  console.log(`  Median: ${ws[Math.floor(ws.length / 2)]} kg`);
  console.log(`  Gjennomsnitt: ${(ws.reduce((s, w) => s + w, 0) / ws.length).toFixed(1)} kg`);

  console.log(`\nMaterialgrupper:`);
  for (const [g, count] of Object.entries(groupCounts).sort((a, b) => b[1] - a[1])) {
    const gChairs = chairs.filter(c => c.materialGroup === g);
    const avgW = gChairs.reduce((s, c) => s + c.estimatedWeight_kg, 0) / gChairs.length;
    console.log(`  ${g}: ${count} stolar, snitt ${avgW.toFixed(1)} kg`);
  }

  // Top 5 heaviest and lightest
  console.log(`\nTopp 5 tyngste:`);
  [...chairs].sort((a, b) => b.estimatedWeight_kg - a.estimatedWeight_kg).slice(0, 5).forEach(c =>
    console.log(`  ${c.objectId}: ${c.estimatedWeight_kg} kg (${c.primaryMaterial}, ${c.year})`)
  );
  console.log(`\nTopp 5 lettaste:`);
  [...chairs].sort((a, b) => a.estimatedWeight_kg - b.estimatedWeight_kg).slice(0, 5).forEach(c =>
    console.log(`  ${c.objectId}: ${c.estimatedWeight_kg} kg (${c.primaryMaterial}, ${c.year})`)
  );

  // Write analysis summary
  const summary = {
    totalChairs: chairs.length,
    yearRange: [Math.min(...chairs.map(c => c.year)), Math.max(...chairs.map(c => c.year))],
    weight: {
      min: ws[0], max: ws[ws.length - 1],
      median: ws[Math.floor(ws.length / 2)],
      mean: +(ws.reduce((s, w) => s + w, 0) / ws.length).toFixed(1),
    },
    materialGroups: Object.entries(groupCounts).map(([g, count]) => ({
      group: g, count,
      avgWeight: +(chairs.filter(c => c.materialGroup === g).reduce((s, c) => s + c.estimatedWeight_kg, 0) / count).toFixed(1),
    })),
    periodWeights: periods.map((p, i) => ({
      period: periodLabels[i],
      avgWeight: periodWeights[i],
      count: periodCounts[i],
    })).filter(p => p.count > 0),
    topHeaviest: [...chairs].sort((a, b) => b.estimatedWeight_kg - a.estimatedWeight_kg).slice(0, 10).map(c => ({
      objectId: c.objectId, title: c.title, weight: c.estimatedWeight_kg, material: c.primaryMaterial, year: c.year,
    })),
    topLightest: [...chairs].sort((a, b) => a.estimatedWeight_kg - b.estimatedWeight_kg).slice(0, 10).map(c => ({
      objectId: c.objectId, title: c.title, weight: c.estimatedWeight_kg, material: c.primaryMaterial, year: c.year,
    })),
  };

  fs.writeFileSync(path.join(BASE_DIR, 'analysis_summary.json'), JSON.stringify(summary, null, 2));
  console.log(`\nSkriven til analysis_summary.json`);
  console.log(`\n7 diagram genererte i ${CHARTS_DIR}/`);
}

main().catch(e => console.error(e));
