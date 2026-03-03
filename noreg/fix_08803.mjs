/**
 * fix_08803.mjs — Process OK-08803 at the raw GLB binary level
 * since gltf-transform can't load it. Reads accessor data directly
 * from the binary buffer.
 */
import { readFileSync, writeFileSync } from 'fs';
import { join, resolve } from 'path';

const noreg = resolve(import.meta.dirname);
const mainPath = join(noreg, 'OK-08803/OK-08803_07518.glb');
const sourcePath = mainPath;
const outputPath = mainPath;

// Target: H 72.5 x B 60.5 x D 44 cm
const targetH = 72.5 / 100; // meters

console.log('Reading GLB...');
const buf = readFileSync(sourcePath);

// Parse GLB header
const magic = buf.toString('ascii', 0, 4);
if (magic !== 'glTF') throw new Error('Not a GLB');
const version = buf.readUInt32LE(4);
const totalLength = buf.readUInt32LE(8);

// Chunk 0: JSON
const chunk0Len = buf.readUInt32LE(12);
const chunk0Type = buf.readUInt32LE(16);
const jsonStr = buf.toString('utf-8', 20, 20 + chunk0Len);
const gltf = JSON.parse(jsonStr);

// Chunk 1: BIN
const binOffset = 20 + chunk0Len;
const chunk1Len = buf.readUInt32LE(binOffset);
const chunk1Type = buf.readUInt32LE(binOffset + 4);
const binStart = binOffset + 8;
const binData = buf.subarray(binStart, binStart + chunk1Len);

console.log(`GLB v${version}, JSON: ${chunk0Len}B, BIN: ${chunk1Len}B`);

// Component type sizes
const COMP_SIZES = { 5120: 1, 5121: 1, 5122: 2, 5123: 2, 5126: 4 };
const TYPE_COUNTS = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4, MAT2: 4, MAT3: 9, MAT4: 16 };

// Find all POSITION accessors and compute bounds
const accessors = gltf.accessors || [];
const bufferViews = gltf.bufferViews || [];
const meshes = gltf.meshes || [];

// Collect POSITION accessor indices
const posAccessorIndices = new Set();
for (const mesh of meshes) {
  for (const prim of mesh.primitives || []) {
    const attrs = prim.attributes || {};
    if (attrs.POSITION !== undefined) {
      posAccessorIndices.add(attrs.POSITION);
    }
  }
}

console.log(`Found ${posAccessorIndices.size} POSITION accessors`);

// Read float32 positions from binary buffer
function getPositionData(accIdx) {
  const acc = accessors[accIdx];
  const bv = bufferViews[acc.bufferView];
  const byteOffset = (bv.byteOffset || 0) + (acc.byteOffset || 0);
  const count = acc.count;
  const byteStride = bv.byteStride || 12; // 3 floats * 4 bytes

  const positions = new Float64Array(count * 3);
  for (let i = 0; i < count; i++) {
    const off = byteOffset + i * byteStride;
    positions[i * 3]     = binData.readFloatLE(off);
    positions[i * 3 + 1] = binData.readFloatLE(off + 4);
    positions[i * 3 + 2] = binData.readFloatLE(off + 8);
  }
  return { positions, count, byteOffset, byteStride };
}

// Compute global bounds
let minX = Infinity, minY = Infinity, minZ = Infinity;
let maxX = -Infinity, maxY = -Infinity, maxZ = -Infinity;

const posData = [];
for (const idx of posAccessorIndices) {
  const pd = getPositionData(idx);
  posData.push({ idx, ...pd });

  for (let i = 0; i < pd.count; i++) {
    const x = pd.positions[i * 3];
    const y = pd.positions[i * 3 + 1];
    const z = pd.positions[i * 3 + 2];
    if (x < minX) minX = x; if (x > maxX) maxX = x;
    if (y < minY) minY = y; if (y > maxY) maxY = y;
    if (z < minZ) minZ = z; if (z > maxZ) maxZ = z;
  }
}

const currentH = maxY - minY;
const sf = targetH / currentH;
const cx = (minX + maxX) / 2;
const cy = minY;
const cz = (minZ + maxZ) / 2;

console.log(`Current: H ${(currentH*100).toFixed(1)}cm`);
console.log(`Scale factor: ${sf.toFixed(4)}`);

// Write transformed positions back into the binary buffer
for (const pd of posData) {
  const acc = accessors[pd.idx];
  const bv = bufferViews[acc.bufferView];
  const baseOffset = (bv.byteOffset || 0) + (acc.byteOffset || 0);
  const byteStride = bv.byteStride || 12;

  let newMinX = Infinity, newMinY = Infinity, newMinZ = Infinity;
  let newMaxX = -Infinity, newMaxY = -Infinity, newMaxZ = -Infinity;

  for (let i = 0; i < pd.count; i++) {
    const off = baseOffset + i * byteStride;
    const nx = (pd.positions[i * 3] - cx) * sf;
    const ny = (pd.positions[i * 3 + 1] - cy) * sf;
    const nz = (pd.positions[i * 3 + 2] - cz) * sf;

    binData.writeFloatLE(nx, off);
    binData.writeFloatLE(ny, off + 4);
    binData.writeFloatLE(nz, off + 8);

    if (nx < newMinX) newMinX = nx; if (nx > newMaxX) newMaxX = nx;
    if (ny < newMinY) newMinY = ny; if (ny > newMaxY) newMaxY = ny;
    if (nz < newMinZ) newMinZ = nz; if (nz > newMaxZ) newMaxZ = nz;
  }

  // Update accessor min/max
  acc.min = [newMinX, newMinY, newMinZ];
  acc.max = [newMaxX, newMaxY, newMaxZ];
}

// Rebuild GLB
const newJsonStr = JSON.stringify(gltf);
let jsonBuf = Buffer.from(newJsonStr, 'utf-8');
// Pad to 4-byte alignment
while (jsonBuf.length % 4 !== 0) {
  jsonBuf = Buffer.concat([jsonBuf, Buffer.from(' ')]);
}

// Pad BIN to 4-byte alignment
let binBuf = Buffer.from(binData);
while (binBuf.length % 4 !== 0) {
  binBuf = Buffer.concat([binBuf, Buffer.from([0])]);
}

const newTotal = 12 + 8 + jsonBuf.length + 8 + binBuf.length;
const out = Buffer.alloc(newTotal);

// Header
out.write('glTF', 0, 'ascii');
out.writeUInt32LE(2, 4);
out.writeUInt32LE(newTotal, 8);

// JSON chunk
out.writeUInt32LE(jsonBuf.length, 12);
out.writeUInt32LE(0x4E4F534A, 16);
jsonBuf.copy(out, 20);

// BIN chunk
const binChunkStart = 20 + jsonBuf.length;
out.writeUInt32LE(binBuf.length, binChunkStart);
out.writeUInt32LE(0x004E4942, binChunkStart + 4);
binBuf.copy(out, binChunkStart + 8);

writeFileSync(outputPath, out);

const resultH = targetH * 100;
console.log(`Result: H ${resultH.toFixed(1)}cm, Origin: bottom-center`);
console.log('Done!');
