// Shared client/server protocol types.

export type ChairKind = 0 | 1 | 2 | 3 | 4 | 5; // 6 procedural chair archetypes

export interface PlayerState {
  id: string;
  name: string;
  kind: ChairKind;
  color: string;
  x: number; y: number; z: number;
  yaw: number;
  score: number;     // total score
  stack: { chairId: string; glbPath: string }[]; // actual chairs in stack
  ready: boolean;
  alive: boolean;
}

export type Phase =
  | { kind: 'lobby' }
  | { kind: 'countdown'; arenaIdx: number; remainingMs: number }
  | { kind: 'arena'; arenaIdx: number; arenaId: ArenaId; remainingMs: number; data: ArenaData }
  | { kind: 'results'; arenaIdx: number; arenaId: ArenaId; standings: StandingRow[] };

export type ArenaId = 'stable';

export type TargetRule =
  | { kind: 'before'; year: number }
  | { kind: 'after'; year: number }
  | { kind: 'between'; from: number; to: number }
  | { kind: 'mat'; mat: 'tre' | 'metall' | 'plast' | 'lær' | 'tekstil' }
  | { kind: 'stil'; stil: string }
  | { kind: 'nat'; nat: string };

export interface PickupItem {
  pid: string;       // pickup id
  chairId: string;   // STOLAR Objekt-ID
  glbPath: string;   // URL to fetch the GLB (e.g. /pbr/opsvik.glb)
  year: number;
  mat: string;
  stil: string;
  nat: string | null;
  x: number;
  z: number;
  takenBy?: string;  // player id
  droppedAt?: number;
  availableAt?: number;
  dropYaw?: number;
}

export interface StableData {
  targets: Record<string, TargetRule>;   // playerId → target
  pickups: PickupItem[];
}

export type ArenaData = StableData;

export interface StandingRow {
  id: string;
  name: string;
  score: number;
  delta: number;
}

// ─── client → server ────────────────────────────────────────
export type ClientMsg =
  | { t: 'hello'; name: string; kind: ChairKind; color: string }
  | { t: 'input'; x: number; y: number; z: number; yaw: number; ts: number }
  | { t: 'ready'; ready: boolean }
  | { t: 'pickup'; pid: string }
  | { t: 'bump'; otherId: string; intensity: number };

// ─── server → client ────────────────────────────────────────
export type ServerMsg =
  | { t: 'welcome'; id: string; players: PlayerState[]; phase: Phase }
  | { t: 'state'; players: PlayerState[]; phase: Phase; ts: number }
  | { t: 'phase'; phase: Phase }
  | { t: 'pickup-result'; pid: string; matched: boolean; chairId: string; glbPath: string; reason: string }
  | { t: 'trip'; victimId: string; victimName: string; byId: string | null; byName: string | null; dropped: number }
  | { t: 'chat'; from: string; text: string };

export const SERVER_HZ = 20;  // server broadcasts state at 20 Hz
export const CLIENT_HZ = 30;  // client sends input at 30 Hz
