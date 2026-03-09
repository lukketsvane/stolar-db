import { NodeIO } from '@gltf-transform/core';
import { KHRDracoMeshCompression, ALL_EXTENSIONS } from '@gltf-transform/extensions';
import { weld, simplify, dedup, prune, textureCompress, quantize } from '@gltf-transform/functions';
import { MeshoptSimplifier } from 'meshoptimizer';
import draco3d from 'draco3dgltf';
import sharp from 'sharp';
import fs from 'fs';
import path from 'path';

const BASE_DIR = 'C:/Users/Shadow/Desktop/stolar-db/noreg';
const OUT_DIR = 'C:/Users/Shadow/Desktop/stolar-db/noreg-optimized';
const TARGET_MB = 5;
const MAX_TEXTURE_SIZE = 1024;

// Adaptive simplify: aggressively reduce based on original face count
function getSimplifyRatio(faceCount) {
  // Target ~30k faces for all models
  const targetFaces = 30000;
  if (faceCount <= targetFaces) return 1.0; // don't simplify small meshes
  return targetFaces / faceCount;
}

async function optimizeFile(glbPath, outPath) {
  await MeshoptSimplifier.ready;

  const decoderModule = await draco3d.createDecoderModule();
  const encoderModule = await draco3d.createEncoderModule();

  const io = new NodeIO()
    .registerExtensions(ALL_EXTENSIONS)
    .registerDependencies({
      'draco3d.decoder': decoderModule,
      'draco3d.encoder': encoderModule,
    });

  const doc = await io.read(glbPath);
  const root = doc.getRoot();

  // Count original faces
  let origFaces = 0;
  root.listMeshes().forEach(mesh => {
    mesh.listPrimitives().forEach(prim => {
      const idx = prim.getIndices();
      if (idx) origFaces += idx.getCount() / 3;
    });
  });

  const ratio = getSimplifyRatio(origFaces);

  // 1. Dedup
  await doc.transform(dedup());

  // 2. Weld vertices
  await doc.transform(weld({ tolerance: 0.0001 }));

  // 3. Simplify meshes (adaptive ratio)
  await doc.transform(
    simplify({ simplifier: MeshoptSimplifier, ratio, error: 0.01 })
  );

  // 4. Resize + compress textures to WebP
  await doc.transform(
    textureCompress({
      encoder: sharp,
      targetFormat: 'webp',
      resize: [MAX_TEXTURE_SIZE, MAX_TEXTURE_SIZE],
      quality: 75,
    })
  );

  // 5. Quantize vertex attributes for smaller binary
  await doc.transform(quantize());

  // 6. Prune unused
  await doc.transform(prune());

  // 7. Enable Draco compression
  doc.createExtension(KHRDracoMeshCompression).setRequired(true).setEncoderOptions({
    method: KHRDracoMeshCompression.EncoderMethod.EDGEBREAKER,
    encodeSpeed: 5,
    decodeSpeed: 5,
    quantizePosition: 14,
    quantizeNormal: 10,
    quantizeTexcoord: 12,
  });

  // Write output
  const outDir = path.dirname(outPath);
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir, { recursive: true });

  await io.write(outPath, doc);

  return fs.statSync(outPath).size / (1024 * 1024);
}

async function main() {
  if (!fs.existsSync(OUT_DIR)) fs.mkdirSync(OUT_DIR, { recursive: true });

  const dirs = fs.readdirSync(BASE_DIR).filter(d => {
    const p = path.join(BASE_DIR, d);
    return fs.statSync(p).isDirectory() && d !== 'node_modules' && d !== 'noreg-optimized' && d !== 'remaining';
  });

  const singleId = process.argv[2];
  const toProcess = singleId ? dirs.filter(d => d === singleId) : dirs;

  console.log(`Processing ${toProcess.length} folders...`);

  const results = [];
  for (let i = 0; i < toProcess.length; i++) {
    const dir = toProcess[i];
    const fullDir = path.join(BASE_DIR, dir);
    const glbs = fs.readdirSync(fullDir).filter(f => f.endsWith('.glb'));
    if (glbs.length === 0) continue;

    const glbPath = path.join(fullDir, glbs[0]);
    const origSizeMB = fs.statSync(glbPath).size / (1024 * 1024);
    const outPath = path.join(OUT_DIR, dir, glbs[0]);

    try {
      const newSizeMB = await optimizeFile(glbPath, outPath);
      const reduction = ((1 - newSizeMB / origSizeMB) * 100).toFixed(0);
      const status = newSizeMB <= TARGET_MB ? 'OK' : 'OVER';
      console.log(`[${i + 1}/${toProcess.length}] ${dir}: ${origSizeMB.toFixed(1)} -> ${newSizeMB.toFixed(1)} MB (${reduction}% reduction) ${status}`);
      results.push({ id: dir, origMB: +origSizeMB.toFixed(1), newMB: +newSizeMB.toFixed(1), reduction: +reduction, status });
    } catch (e) {
      console.error(`[${i + 1}/${toProcess.length}] ${dir}: ERROR - ${e.message}`);
      results.push({ id: dir, origMB: +origSizeMB.toFixed(1), error: e.message });
    }
  }

  const ok = results.filter(r => r.status === 'OK');
  const over = results.filter(r => r.status === 'OVER');
  const errors = results.filter(r => r.error);
  console.log(`\n=== RESULTS ===`);
  console.log(`OK (<=5MB): ${ok.length}`);
  console.log(`OVER (>5MB): ${over.length}`);
  if (over.length > 0) console.log('Over files:', over.map(r => `${r.id} (${r.newMB}MB)`).join(', '));
  console.log(`Errors: ${errors.length}`);
  if (errors.length > 0) console.log('Error files:', errors.map(r => `${r.id}: ${r.error}`).join('\n'));

  const totalOrig = results.reduce((s, r) => s + r.origMB, 0);
  const totalNew = results.filter(r => r.newMB).reduce((s, r) => s + r.newMB, 0);
  console.log(`Total: ${totalOrig.toFixed(0)} MB -> ${totalNew.toFixed(0)} MB`);

  fs.writeFileSync(path.join(OUT_DIR, 'results.json'), JSON.stringify(results, null, 2));
}

main().catch(e => console.error(e));
