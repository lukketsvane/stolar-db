/**
 * scale_and_center.mjs — Scale GLB models to real-world height,
 * center XZ, and set origin to the lowest point of geometry.
 *
 * Uses _original.glb as source (if it exists), writes to the main .glb.
 * Uniform scale based on height so proportions are preserved.
 */
import { readFileSync, writeFileSync, readdirSync, existsSync } from 'fs';
import { join, resolve } from 'path';
import { NodeIO } from '@gltf-transform/core';

const noreg = resolve(import.meta.dirname);
const data = JSON.parse(readFileSync(join(noreg, 'nasjonalmuseet_stoler_128.json'), 'utf-8'));

// ── Parse dimensions ──────────────────────────────────────────
function parseDimensionsCm(malStr) {
  if (!malStr) return null;
  // Normalize: remove spaces inside numbers ("117, 5" -> "117,5"), extra "x" ("B x 49" -> "B 49")
  let s = String(malStr).replace(/(\d),\s+(\d)/g, '$1,$2').replace(/B\s*x\s*(\d)/g, 'B $1');

  // Pattern: "H 95,5 x B 50,5 x D 49 cm"
  let m = s.match(/H\s*([\d]+[,.]?\d*)\s*(?:cm\s*)?x\s*,?\s*B\s*([\d]+[,.]?\d*)\s*(?:cm\s*)?x\s*D\s*([\d]+[,.]?\d*)/);
  if (m) {
    return {
      h: parseFloat(m[1].replace(',', '.')),
      b: parseFloat(m[2].replace(',', '.')),
      d: parseFloat(m[3].replace(',', '.'))
    };
  }

  // Pattern: "139 x 70,5 x 70 cm"
  m = s.match(/([\d]+[,.]?\d*)\s*x\s*([\d]+[,.]?\d*)\s*x\s*([\d]+[,.]?\d*)\s*cm/);
  if (m) {
    return {
      h: parseFloat(m[1].replace(',', '.')),
      b: parseFloat(m[2].replace(',', '.')),
      d: parseFloat(m[3].replace(',', '.'))
    };
  }

  // Pattern: "H 107 x ⌀ 62 cm"
  m = s.match(/H\s*([\d]+[,.]?\d*)\s*x\s*[⌀Ø]\s*([\d]+[,.]?\d*)\s*cm/);
  if (m) {
    const h = parseFloat(m[1].replace(',', '.'));
    const diam = parseFloat(m[2].replace(',', '.'));
    return { h, b: diam, d: diam };
  }

  return null;
}

// ── Compute bounding box from all mesh primitives ─────────────
function computeBounds(document) {
  const min = [Infinity, Infinity, Infinity];
  const max = [-Infinity, -Infinity, -Infinity];

  for (const mesh of document.getRoot().listMeshes()) {
    for (const prim of mesh.listPrimitives()) {
      const posAccessor = prim.getAttribute('POSITION');
      if (!posAccessor) continue;

      const posArray = posAccessor.getArray();
      const count = posAccessor.getCount();

      for (let i = 0; i < count; i++) {
        const x = posArray[i * 3];
        const y = posArray[i * 3 + 1];
        const z = posArray[i * 3 + 2];
        if (x < min[0]) min[0] = x;
        if (y < min[1]) min[1] = y;
        if (z < min[2]) min[2] = z;
        if (x > max[0]) max[0] = x;
        if (y > max[1]) max[1] = y;
        if (z > max[2]) max[2] = z;
      }
    }
  }

  return { min, max };
}

// ── Transform all vertex positions in-place ───────────────────
function transformPositions(document, scaleFactor, offsetX, offsetY, offsetZ) {
  // Track which accessors we've already modified so we
  // don't double-transform shared ones.
  const processed = new Set();

  for (const mesh of document.getRoot().listMeshes()) {
    for (const prim of mesh.listPrimitives()) {
      const posAccessor = prim.getAttribute('POSITION');
      if (!posAccessor) continue;
      if (processed.has(posAccessor)) continue;
      processed.add(posAccessor);

      const count = posAccessor.getCount();
      for (let i = 0; i < count; i++) {
        const el = posAccessor.getElement(i, [0, 0, 0]);
        el[0] = (el[0] + offsetX) * scaleFactor;
        el[1] = (el[1] + offsetY) * scaleFactor;
        el[2] = (el[2] + offsetZ) * scaleFactor;
        posAccessor.setElement(i, el);
      }
    }
  }
}

// ── Clear all node transforms (bake to identity) ─────────────
function clearNodeTransforms(document) {
  for (const node of document.getRoot().listNodes()) {
    node.setTranslation([0, 0, 0]);
    node.setRotation([0, 0, 0, 1]);
    node.setScale([1, 1, 1]);
    if (node.getMatrix()) {
      node.setMatrix([
        1, 0, 0, 0,
        0, 1, 0, 0,
        0, 0, 1, 0,
        0, 0, 0, 1
      ]);
    }
  }
}

// ── Main ──────────────────────────────────────────────────────
const io = new NodeIO();

// Build lookup: objectId -> dims
const dimsMap = new Map();
for (const chair of data) {
  const dims = parseDimensionsCm(chair['Mål']);
  if (dims) dimsMap.set(chair.objectId, dims);
}

console.log('='.repeat(65));
console.log('  Scale & Center GLB models to real-world dimensions');
console.log('='.repeat(65));
console.log(`  Loaded dimensions for ${dimsMap.size} chairs`);
console.log();

let scaled = 0;
let skipped = 0;
const errors = [];

// Process each chair folder
const folders = readdirSync(noreg, { withFileTypes: true })
  .filter(d => d.isDirectory() && !d.name.startsWith('.') && d.name !== 'node_modules' && d.name !== '__pycache__')
  .map(d => d.name)
  .sort();

for (const folderName of folders) {
  const folder = join(noreg, folderName);
  const files = readdirSync(folder);

  // Find the main GLB (not _original)
  const mainGlb = files.find(f => f.endsWith('.glb') && !f.includes('_original'));
  if (!mainGlb) {
    continue; // not a chair folder
  }

  // Derive the object ID from the folder name
  const objId = folderName;

  if (!dimsMap.has(objId)) {
    console.log(`  SKIP     ${objId} — no dimensions in data`);
    skipped++;
    continue;
  }

  // Use _original as source if available, else main
  const originalGlb = files.find(f => f.endsWith('_original.glb'));
  const sourcePath = originalGlb ? join(folder, originalGlb) : join(folder, mainGlb);
  const outputPath = join(folder, mainGlb);

  const dims = dimsMap.get(objId);
  const targetHeightM = dims.h / 100; // cm -> meters (glTF uses meters)

  try {
    const document = await io.read(sourcePath);

    // 1. Get current bounds
    const bounds = computeBounds(document);
    const currentHeight = bounds.max[1] - bounds.min[1];
    const currentWidth = bounds.max[0] - bounds.min[0];
    const currentDepth = bounds.max[2] - bounds.min[2];

    if (currentHeight <= 0) {
      console.log(`  SKIP     ${objId} — zero height in model`);
      skipped++;
      continue;
    }

    // 2. Uniform scale factor based on height
    const scaleFactor = targetHeightM / currentHeight;

    // 3. Compute offsets to center XZ and put bottom at Y=0
    //    We offset BEFORE scaling: shift so that center XZ -> 0, min Y -> 0
    const centerX = (bounds.min[0] + bounds.max[0]) / 2;
    const centerZ = (bounds.min[2] + bounds.max[2]) / 2;
    const bottomY = bounds.min[1];

    const offsetX = -centerX;
    const offsetY = -bottomY;
    const offsetZ = -centerZ;

    // 4. Apply transform directly to vertex data
    transformPositions(document, scaleFactor, offsetX, offsetY, offsetZ);

    // 5. Verify
    const newBounds = computeBounds(document);
    const newHeight = (newBounds.max[1] - newBounds.min[1]) * 100; // back to cm
    const newWidth = (newBounds.max[0] - newBounds.min[0]) * 100;
    const newDepth = (newBounds.max[2] - newBounds.min[2]) * 100;

    console.log(`  SCALE    ${objId}`);
    console.log(`           Source: ${currentHeight * 100 | 0}cm x ${currentWidth * 100 | 0}cm x ${currentDepth * 100 | 0}cm`);
    console.log(`           Target: H ${dims.h} x B ${dims.b} x D ${dims.d} cm`);
    console.log(`           Result: H ${newHeight.toFixed(1)} x B ${newWidth.toFixed(1)} x D ${newDepth.toFixed(1)} cm`);
    console.log(`           Factor: ${scaleFactor.toFixed(4)}, Origin: bottom-center`);

    // 6. Write output
    await io.write(outputPath, document);
    scaled++;

  } catch (e) {
    console.log(`  ERROR    ${objId} — ${e.message}`);
    errors.push({ id: objId, error: e.message });
  }
}

console.log();
console.log('='.repeat(65));
console.log(`  Done! Scaled ${scaled} models, skipped ${skipped}`);
if (errors.length) {
  console.log(`  Errors: ${errors.length}`);
  for (const { id, error } of errors) {
    console.log(`    ${id}: ${error}`);
  }
}
console.log('='.repeat(65));
