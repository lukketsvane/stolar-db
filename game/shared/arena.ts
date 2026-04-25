export interface StableObstacle {
  id: string;
  x: number;
  z: number;
  w: number;
  d: number;
  yaw: number;
  color: string;
}

export const STABLE_ARENA = {
  halfX: 24,
  halfZ: 28,
  wallHeight: 2.2,
  spawnZ: 22,
  spawnXStart: -8,
  spawnSpacing: 4,
  pickupMargin: 3,
} as const;

export const STABLE_OBSTACLES: StableObstacle[] = [
  { id: 'top-left-gate', x: -8.5, z: 10.5, w: 13, d: 1.2, yaw: 0.36, color: '#FFD56B' },
  { id: 'top-right-gate', x: 8.5, z: 5.5, w: 13, d: 1.2, yaw: -0.36, color: '#FF7FA5' },
  { id: 'mid-left-gate', x: -8, z: -4, w: 12, d: 1.2, yaw: -0.32, color: '#61D4E8' },
  { id: 'mid-right-gate', x: 8, z: -11.5, w: 12, d: 1.2, yaw: 0.32, color: '#9C8CFF' },
  { id: 'center-block', x: 0, z: 1.2, w: 4.2, d: 4.2, yaw: 0.78, color: '#FF8A5B' },
  { id: 'low-block', x: 0, z: -19, w: 7.2, d: 1.4, yaw: 0, color: '#83D889' },
];

export function stableSpawnPosition(index: number) {
  const columns = 5;
  const row = Math.floor(index / columns);
  return {
    x: STABLE_ARENA.spawnXStart + (index % columns) * STABLE_ARENA.spawnSpacing,
    y: 1,
    z: STABLE_ARENA.spawnZ - row * 3,
    yaw: Math.PI,
  };
}

export function isInsideStableObstacle(x: number, z: number, padding = 0): boolean {
  return STABLE_OBSTACLES.some((o) => {
    const cos = Math.cos(-o.yaw);
    const sin = Math.sin(-o.yaw);
    const dx = x - o.x;
    const dz = z - o.z;
    const localX = dx * cos - dz * sin;
    const localZ = dx * sin + dz * cos;
    return Math.abs(localX) <= o.w / 2 + padding && Math.abs(localZ) <= o.d / 2 + padding;
  });
}
