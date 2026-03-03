import { NodeIO } from '@gltf-transform/core';
import { ALL_EXTENSIONS } from '@gltf-transform/extensions';
import fs from 'fs';
import path from 'path';

const PROJECT_ROOT = 'C:/Users/Shadow/Desktop/stolar-db';
const SOURCE = process.argv.includes('--source')
  ? process.argv[process.argv.indexOf('--source') + 1]
  : 'noreg';

const BASE_DIR = SOURCE === 'nm_stolar'
  ? path.join(PROJECT_ROOT, 'NM_stolar')
  : path.join(PROJECT_ROOT, 'noreg');
const MASTER_JSON = SOURCE === 'nm_stolar'
  ? path.join(BASE_DIR, 'NM_stolar.json')
  : path.join(BASE_DIR, 'nasjonalmuseet_stoler_128.json');

// Material density in kg/m³ (average values)
const MATERIAL_DENSITY = {
  // Hardwood
  'Eik': 660, 'Mahogni': 550, 'Bøk': 660, 'Ask': 590, 'Bjørk': 640,
  'Alm': 560, 'Jakaranda': 850, 'Buksbom': 900, 'Or': 530,
  'Palme': 500, 'Whitewood': 420,
  // Softwood
  'Furu': 450, 'Gran': 420,
  // Generic wood
  'Tre': 550, 'Kryssfiner': 550,
  // Metal
  'Stål': 7850, 'Stålrør': 7850, 'Jern': 7870,
  'Messing': 8500, 'Bronse': 8800, 'Metall': 7850,
  // Plastic / Rubber
  'Plast': 1050, 'Gummi': 1150, 'Gummi/plast': 1100,
  'Skumplast': 30, 'Polyuretan': 1200, 'Polyamid': 1140,
  // Textile / Upholstery (effective density with air)
  'Ull': 100, 'Bomull': 120, 'Lin': 120, 'Silke': 80,
  'Tekstil': 100, 'Tekstil, fløyel': 100, 'Tekstil, plysj': 100, 'Plysj': 100,
  'Strie': 100, 'Hestetagl': 150,
  'Animalske fibre, filt': 100,
  'Syntetiske fibre, kunstsilke': 100,
  'Vegetabilske fibre': 100, 'Vegetabilske fibre, stramei': 100, 'Vegetabilske fibre, strie': 100,
  // Leather
  'Lær': 860, 'Skinn/lær/pergament': 860, 'Skinn/lær/pergament, gyllenlær': 860,
  'Annet, kunstlær': 800,
  // Other
  'Voks': 900,
};

// Fill factors per material category (how much of bounding box is solid)
const FILL_FACTORS = {
  wood: 0.10,       // Wood chairs ~10% solid of bbox
  metal_tube: 0.002, // Tubular steel: thin-wall tubes, very little material
  metal_solid: 0.008, // Cast/forged metal chairs still mostly air
  plastic: 0.06,
  upholstered: 0.12, // More filled due to padding
};

function getMaterialCategory(materials) {
  if (!materials || materials.length === 0) return 'wood';
  const structural = getStructuralMaterial(materials);
  if (['Stålrør'].includes(structural)) return 'metal_tube';
  if (['Stål', 'Jern', 'Bronse', 'Metall'].includes(structural)) return 'metal_solid';
  if (['Plast', 'Gummi', 'Gummi/plast', 'Polyuretan', 'Polyamid'].includes(structural)) return 'plastic';
  return 'wood';
}

function getFillFactor(materials, hasUpholstery) {
  const cat = getMaterialCategory(materials);
  if (hasUpholstery && cat === 'wood') return FILL_FACTORS.upholstered;
  return FILL_FACTORS[cat];
}

// Non-structural materials (upholstery, covering, decoration)
const NON_STRUCTURAL = new Set([
  'Ull', 'Bomull', 'Lin', 'Silke', 'Tekstil', 'Tekstil, fløyel', 'Tekstil, plysj',
  'Plysj', 'Strie', 'Hestetagl', 'Skumplast', 'Lær', 'Skinn/lær/pergament',
  'Skinn/lær/pergament, gyllenlær', 'Annet, kunstlær', 'Animalske fibre, filt',
  'Syntetiske fibre, kunstsilke', 'Vegetabilske fibre', 'Vegetabilske fibre, stramei',
  'Vegetabilske fibre, strie', 'Voks', 'Messing', // messing is usually nails/fittings
]);

function getStructuralMaterial(materials) {
  if (!materials || materials.length === 0) return 'Tre';
  const matList = Array.isArray(materials) ? materials : [materials];
  // Find first structural material
  for (const m of matList) {
    if (!NON_STRUCTURAL.has(m)) return m;
  }
  return matList[0]; // fallback to first if all are non-structural
}

function getPrimaryDensity(materials) {
  const structural = getStructuralMaterial(materials);
  return MATERIAL_DENSITY[structural] || 550;
}

// Parse "Mål" field to extract H, B, D in cm
function parseDimensions(maal) {
  if (!maal) return null;

  let H = null, B = null, D = null;

  // Try "H 95,5 x B 50,5 x D 49 cm" format (no unit between values)
  const hbd = maal.match(/H\s*([\d,\.]+)\s*x\s*B\s*([\d,\.]+)\s*x\s*D\s*([\d,\.]+)/i);
  if (hbd) {
    H = parseFloat(hbd[1].replace(',', '.'));
    B = parseFloat(hbd[2].replace(',', '.'));
    D = parseFloat(hbd[3].replace(',', '.'));
  }

  // Try "H 85 cm x B 63 cm x D 55 cm" format (unit between values)
  if (!H) {
    const hbd2 = maal.match(/H\s*([\d,\.]+)\s*cm\s*x\s*B\s*([\d,\.]+)\s*cm\s*x\s*D\s*([\d,\.]+)\s*cm/i);
    if (hbd2) {
      H = parseFloat(hbd2[1].replace(',', '.'));
      B = parseFloat(hbd2[2].replace(',', '.'));
      D = parseFloat(hbd2[3].replace(',', '.'));
    }
  }

  // Try "139 x 70,5 x 70 cm" format (H x B x D assumed)
  if (!H) {
    const xyz = maal.match(/([\d,\.]+)\s*x\s*([\d,\.]+)\s*x\s*([\d,\.]+)\s*cm/i);
    if (xyz) {
      H = parseFloat(xyz[1].replace(',', '.'));
      B = parseFloat(xyz[2].replace(',', '.'));
      D = parseFloat(xyz[3].replace(',', '.'));
    }
  }

  // Fallback: look for individual Høyde/Bredde/Dybde
  if (!H) {
    const hm = maal.match(/Høyde[:\s]*([\d,\.]+)/i);
    if (hm) H = parseFloat(hm[1].replace(',', '.'));
  }
  if (!B) {
    const bm = maal.match(/Bredde[:\s]*([\d,\.]+)/i);
    if (bm) B = parseFloat(bm[1].replace(',', '.'));
  }
  if (!D) {
    const dm = maal.match(/Dybde[:\s]*([\d,\.]+)/i);
    if (dm) D = parseFloat(dm[1].replace(',', '.'));
  }

  if (H && B && D) return { H, B, D };
  return null;
}

// Get bounding box from GLB mesh
function getMeshBoundingBox(doc) {
  const root = doc.getRoot();
  let minX = Infinity, minY = Infinity, minZ = Infinity;
  let maxX = -Infinity, maxY = -Infinity, maxZ = -Infinity;

  for (const mesh of root.listMeshes()) {
    for (const prim of mesh.listPrimitives()) {
      const pos = prim.getAttribute('POSITION');
      if (!pos) continue;
      const count = pos.getCount();
      for (let i = 0; i < count; i++) {
        const [x, y, z] = pos.getElement(i, [0, 0, 0]);
        if (x < minX) minX = x;
        if (y < minY) minY = y;
        if (z < minZ) minZ = z;
        if (x > maxX) maxX = x;
        if (y > maxY) maxY = y;
        if (z > maxZ) maxZ = z;
      }
    }
  }

  if (minX === Infinity) return null;

  return {
    min: [minX, minY, minZ],
    max: [maxX, maxY, maxZ],
    size: [maxX - minX, maxY - minY, maxZ - minZ],
  };
}

// Compute signed volume of mesh (for watertight meshes)
function computeMeshVolume(doc) {
  const root = doc.getRoot();
  let totalVolume = 0;

  for (const mesh of root.listMeshes()) {
    for (const prim of mesh.listPrimitives()) {
      const pos = prim.getAttribute('POSITION');
      const indices = prim.getIndices();
      if (!pos || !indices) continue;

      const triCount = indices.getCount() / 3;
      for (let t = 0; t < triCount; t++) {
        const i0 = indices.getScalar(t * 3);
        const i1 = indices.getScalar(t * 3 + 1);
        const i2 = indices.getScalar(t * 3 + 2);

        const v0 = pos.getElement(i0, [0, 0, 0]);
        const v1 = pos.getElement(i1, [0, 0, 0]);
        const v2 = pos.getElement(i2, [0, 0, 0]);

        // Signed volume of tetrahedron with origin
        totalVolume += (
          v0[0] * (v1[1] * v2[2] - v2[1] * v1[2]) -
          v1[0] * (v0[1] * v2[2] - v2[1] * v0[2]) +
          v2[0] * (v0[1] * v1[2] - v1[1] * v0[2])
        ) / 6.0;
      }
    }
  }

  return Math.abs(totalVolume);
}

function hasUpholsteryMaterials(materials) {
  if (!materials) return false;
  const matList = Array.isArray(materials) ? materials : [materials];
  const upholsteryTerms = ['Ull', 'Bomull', 'Lin', 'Silke', 'Tekstil', 'Plysj', 'Strie',
    'Hestetagl', 'Skumplast', 'Polyuretan', 'Lær', 'Skinn', 'filt', 'kunstlær'];
  return matList.some(m => upholsteryTerms.some(t => m.includes(t)));
}

async function main() {
  console.log(`Source: ${SOURCE} (${MASTER_JSON})`);
  const chairs = JSON.parse(fs.readFileSync(MASTER_JSON, 'utf8'));
  const io = new NodeIO().registerExtensions(ALL_EXTENSIONS);

  const results = [];
  let processed = 0;

  for (const chair of chairs) {
    const { objectId, Materiale, Mål } = chair;
    const matList = Array.isArray(Materiale) ? Materiale : (Materiale ? [Materiale] : []);

    // Find GLB file
    const dirPath = path.join(BASE_DIR, objectId);
    if (!fs.existsSync(dirPath)) {
      console.log(`[SKIP] ${objectId}: no directory`);
      continue;
    }
    const glbs = fs.readdirSync(dirPath).filter(f => f.endsWith('.glb') && !f.includes('_optimized'));
    if (glbs.length === 0) {
      console.log(`[SKIP] ${objectId}: no GLB file`);
      continue;
    }

    const glbPath = path.join(dirPath, glbs[0]);
    const dims = parseDimensions(Mål);

    if (!dims) {
      console.log(`[SKIP] ${objectId}: could not parse dimensions from "${Mål}"`);
      continue;
    }

    try {
      const doc = await io.read(glbPath);
      const bbox = getMeshBoundingBox(doc);
      const meshVolume = computeMeshVolume(doc);

      if (!bbox) {
        console.log(`[SKIP] ${objectId}: no mesh geometry`);
        continue;
      }

      // Physical bbox volume in m³
      const physVolume_m3 = (dims.H / 100) * (dims.B / 100) * (dims.D / 100);

      // Mesh bbox volume (in model units, likely meters)
      const meshBboxVol = bbox.size[0] * bbox.size[1] * bbox.size[2];

      // Scale factor from mesh to physical
      const scaleFactor = meshBboxVol > 0 ? physVolume_m3 / meshBboxVol : 1;

      // Scaled mesh volume in m³
      const scaledMeshVolume = meshVolume * scaleFactor;

      // Mesh fill ratio (mesh volume / bbox volume in mesh space)
      const meshFillRatio = meshBboxVol > 0 ? meshVolume / meshBboxVol : 0.12;

      // Material properties
      const structuralMat = getStructuralMaterial(matList);
      const density = MATERIAL_DENSITY[structuralMat] || 550;
      const hasUpholstery = hasUpholsteryMaterials(matList);
      const fillFactor = getFillFactor(matList, hasUpholstery);

      // Weight estimation: bbox volume * fill factor * density
      // For metal/plastic, mesh fill ratio is misleading (scanned surface != material volume)
      // Only use mesh fill ratio for wood chairs where it can refine the estimate
      const matCat = getMaterialCategory(matList);
      let effectiveFill;
      if (matCat === 'metal_tube' || matCat === 'metal_solid') {
        effectiveFill = fillFactor; // Use category-based fill only
      } else if (matCat === 'plastic') {
        effectiveFill = fillFactor;
      } else {
        // Wood: use mesh fill ratio if reasonable, otherwise category fill
        effectiveFill = Math.max(fillFactor, Math.min(meshFillRatio, 0.20));
      }
      const weightKg = physVolume_m3 * effectiveFill * density;

      // Sanity check bounds
      const clampedWeight = Math.max(1.5, Math.min(weightKg, 80));

      processed++;
      console.log(`[${processed}] ${objectId}: ${dims.H}×${dims.B}×${dims.D}cm, ${structuralMat} (${density} kg/m³), fill=${(effectiveFill*100).toFixed(1)}%, est=${clampedWeight.toFixed(1)} kg`);

      results.push({
        objectId,
        title: chair.title,
        datering: chair.Datering,
        stilperiode: chair.Stilperiode,
        betegnelse: chair.Betegnelse,
        primaryMaterial: structuralMat,
        allMaterials: matList,
        dimensions: dims,
        bboxVolume_m3: +physVolume_m3.toFixed(6),
        meshFillRatio: +meshFillRatio.toFixed(4),
        effectiveFill: +effectiveFill.toFixed(4),
        density_kgm3: density,
        estimatedWeight_kg: +clampedWeight.toFixed(1),
        hasUpholstery,
        meshBbox: bbox.size.map(v => +v.toFixed(4)),
      });
    } catch (e) {
      console.error(`[ERROR] ${objectId}: ${e.message}`);
      results.push({
        objectId,
        title: chair.title,
        error: e.message,
      });
    }
  }

  // Summary statistics
  const valid = results.filter(r => r.estimatedWeight_kg);
  const weights = valid.map(r => r.estimatedWeight_kg);
  const avg = weights.reduce((s, w) => s + w, 0) / weights.length;
  const sorted = [...weights].sort((a, b) => a - b);
  const median = sorted[Math.floor(sorted.length / 2)];
  const min = sorted[0];
  const max = sorted[sorted.length - 1];

  console.log(`\n=== SUMMARY ===`);
  console.log(`Processed: ${valid.length} chairs`);
  console.log(`Weight range: ${min.toFixed(1)} – ${max.toFixed(1)} kg`);
  console.log(`Average: ${avg.toFixed(1)} kg`);
  console.log(`Median: ${median.toFixed(1)} kg`);

  const outPath = path.join(BASE_DIR, 'weight_estimates.json');
  fs.writeFileSync(outPath, JSON.stringify({ summary: { count: valid.length, min, max, avg: +avg.toFixed(1), median }, chairs: results }, null, 2));
  console.log(`\nWritten to ${outPath}`);
}

main().catch(e => console.error(e));
