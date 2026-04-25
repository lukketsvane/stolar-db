// Stolspel multiplayer WebSocket server.
// Mechanic: each player gets a personal target rule. They run around picking
// up chair items that match. Mismatched picks reduce the stack. Final stack
// height when time runs out = score.

import { WebSocketServer, WebSocket } from 'ws';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import type {
  ClientMsg, ServerMsg, PlayerState, Phase, StableData, StandingRow, ChairKind,
  TargetRule, PickupItem,
} from '../shared/protocol.ts';
import { STABLE_ARENA, isInsideStableObstacle, stableSpawnPosition } from '../shared/arena.ts';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const POOL_PATH = path.resolve(__dirname, '..', 'public', 'pbr_pool.json');

interface ChairRow {
  id: string; year: number; namn: string; stil: string;
  mat: string; nat: string | null;
  glbPath: string;
}
// PBR-textured chair pool. Each entry knows its own URL via `glbPath`.
const CHAIRS = JSON.parse(readFileSync(POOL_PATH, 'utf-8')) as ChairRow[];

const PORT = 5176;
const TICK_MS = 50;
const COUNTDOWN_MS = 4000;
const ARENA_MS = 60_000;
const RESULTS_MS = 8000;
const MIN_PLAYERS_TO_START = 1;
const PICKUP_RADIUS = 1.6;
const ARENA_HALF_X = STABLE_ARENA.halfX;
const ARENA_HALF_Z = STABLE_ARENA.halfZ;
const PICKUP_MIN_SPACING = 3.2;

interface Conn {
  ws: WebSocket;
  player: PlayerState;
  lastInput: number;
  lastBumpAt: number;
}

const conns = new Map<string, Conn>();

let phase: Phase = { kind: 'lobby' };
let phaseChangedAt = Date.now();

function uid(): string {
  return Math.random().toString(36).slice(2, 8);
}

function send(ws: WebSocket, msg: ServerMsg) {
  if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(msg));
}

function broadcast(msg: ServerMsg) {
  const s = JSON.stringify(msg);
  for (const c of conns.values()) if (c.ws.readyState === WebSocket.OPEN) c.ws.send(s);
}

function snapshotPlayers(): PlayerState[] {
  return [...conns.values()].map((c) => c.player);
}

function snapshotMsg(): ServerMsg {
  return { t: 'state', players: snapshotPlayers(), phase, ts: Date.now() };
}

function setPhase(next: Phase) {
  phase = next;
  phaseChangedAt = Date.now();
  broadcast({ t: 'phase', phase });
}

// ─── target generation ──────────────────────────────────────

const STIL_OPTIONS = ['Barokk', 'Rokokko', 'Nyklassisisme', 'Empire', 'Modernisme', 'Postmodernisme', 'Historisme'];
const NAT_OPTIONS = ['Noreg', 'Sverige', 'Danmark', 'Tyskland', 'England', 'Frankrike', 'Italia'];
const MAT_OPTIONS: Array<'tre' | 'metall' | 'plast' | 'lær' | 'tekstil'> = ['tre', 'metall'];
const YEAR_BREAKS = [1700, 1800, 1850, 1900, 1950];

// Generate a target rule that has at least N matching chairs in the pool.
function makeTarget(rng: () => number, takenStils: Set<string>, takenNats: Set<string>): TargetRule {
  const candidates: TargetRule[] = [];
  for (const y of YEAR_BREAKS) {
    candidates.push({ kind: 'before', year: y });
    candidates.push({ kind: 'after', year: y });
  }
  for (const m of MAT_OPTIONS) candidates.push({ kind: 'mat', mat: m });
  for (const s of STIL_OPTIONS) if (!takenStils.has(s)) candidates.push({ kind: 'stil', stil: s });
  for (const n of NAT_OPTIONS) if (!takenNats.has(n)) candidates.push({ kind: 'nat', nat: n });

  // shuffle
  for (let i = candidates.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [candidates[i], candidates[j]] = [candidates[j], candidates[i]];
  }
  // pick first candidate with >= 3 matches in pool
  for (const t of candidates) {
    const n = CHAIRS.filter((c) => matches(t, c)).length;
    if (n >= 3) {
      if (t.kind === 'stil') takenStils.add(t.stil);
      if (t.kind === 'nat') takenNats.add(t.nat);
      return t;
    }
  }
  return { kind: 'mat', mat: 'tre' };
}

function matches(target: TargetRule, c: ChairRow): boolean {
  switch (target.kind) {
    case 'before': return c.year < target.year;
    case 'after': return c.year > target.year;
    case 'between': return c.year >= target.from && c.year <= target.to;
    case 'mat': return c.mat === target.mat;
    case 'stil': return c.stil === target.stil;
    case 'nat': return (c.nat ?? '').toLowerCase() === target.nat.toLowerCase();
  }
}

// ─── arena setup ────────────────────────────────────────────

function lcg(seed: number): () => number {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

function placePickup(rng: () => number, placed: PickupItem[]): { x: number; z: number } {
  const margin = STABLE_ARENA.pickupMargin;
  for (let attempt = 0; attempt < 80; attempt++) {
    const x = (rng() * 2 - 1) * (ARENA_HALF_X - margin);
    const z = (rng() * 2 - 1) * (ARENA_HALF_Z - margin);
    if (z > STABLE_ARENA.spawnZ - 6) continue;
    if (isInsideStableObstacle(x, z, 1.8)) continue;
    if (placed.some((p) => {
      const dx = p.x - x;
      const dz = p.z - z;
      return dx * dx + dz * dz < PICKUP_MIN_SPACING * PICKUP_MIN_SPACING;
    })) continue;
    return { x, z };
  }
  return {
    x: (rng() * 2 - 1) * (ARENA_HALF_X - margin),
    z: -ARENA_HALF_Z + margin + rng() * (ARENA_HALF_Z * 1.2),
  };
}

function startCountdown(arenaIdx: number) {
  setPhase({ kind: 'countdown', arenaIdx, remainingMs: COUNTDOWN_MS });
}

function startArena(arenaIdx: number) {
  const rng = lcg(Date.now());
  const targets: Record<string, TargetRule> = {};
  const takenStils = new Set<string>();
  const takenNats = new Set<string>();
  for (const c of conns.values()) {
    targets[c.player.id] = makeTarget(rng, takenStils, takenNats);
    c.player.score = 0;
  }

  // 17 unique chairs in pool. We render each ONCE — every dynamic rigid
  // body with a high-poly PBR mesh is expensive, so keep the count low.
  const picked: ChairRow[] = CHAIRS.slice();
  // shuffle
  for (let i = picked.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [picked[i], picked[j]] = [picked[j], picked[i]];
  }

  const pickups: PickupItem[] = [];
  picked.forEach((c, i) => {
    const pos = placePickup(rng, pickups);
    pickups.push({
      pid: `p${i}`,
      chairId: c.id,
      glbPath: c.glbPath,
      year: c.year,
      mat: c.mat,
      stil: c.stil,
      nat: c.nat,
      x: pos.x,
      z: pos.z,
    });
  });

  const data: StableData = { targets, pickups };
  respawnAll();
  setPhase({ kind: 'arena', arenaIdx, arenaId: 'stable', remainingMs: ARENA_MS, data });
}

function endArena() {
  if (phase.kind !== 'arena') return;
  const standings: StandingRow[] = [];
  for (const c of conns.values()) {
    standings.push({ id: c.player.id, name: c.player.name, score: c.player.score, delta: c.player.score });
  }
  standings.sort((a, b) => b.delta - a.delta);
  setPhase({ kind: 'results', arenaIdx: phase.arenaIdx, arenaId: phase.arenaId, standings });
}

function tick() {
  const now = Date.now();
  const elapsed = now - phaseChangedAt;

  if (phase.kind === 'lobby') {
    const ready = [...conns.values()].filter((c) => c.player.ready).length;
    if (ready >= MIN_PLAYERS_TO_START && conns.size >= MIN_PLAYERS_TO_START) {
      startCountdown(0);
    }
  } else if (phase.kind === 'countdown') {
    const remaining = Math.max(0, COUNTDOWN_MS - elapsed);
    phase.remainingMs = remaining;
    if (remaining === 0) startArena(phase.arenaIdx);
  } else if (phase.kind === 'arena') {
    const remaining = Math.max(0, ARENA_MS - elapsed);
    phase.remainingMs = remaining;
    if (remaining === 0) endArena();
  } else if (phase.kind === 'results') {
    if (elapsed > RESULTS_MS) {
      for (const c of conns.values()) c.player.ready = false;
      setPhase({ kind: 'lobby' });
    }
  }

  broadcast(snapshotMsg());
}

function pickupReason(target: TargetRule | undefined, item: PickupItem): string {
  if (!target) return 'no-target';
  switch (target.kind) {
    case 'before': return `${item.year} ≥ ${target.year}`;
    case 'after': return `${item.year} ≤ ${target.year}`;
    case 'between': return `${item.year} ikkje i [${target.from}, ${target.to}]`;
    case 'mat': return `${item.mat} ≠ ${target.mat}`;
    case 'stil': return `${item.stil} ≠ ${target.stil}`;
    case 'nat': return `${item.nat ?? '?'} ≠ ${target.nat}`;
  }
}

function handleMsg(c: Conn, raw: ClientMsg) {
  switch (raw.t) {
    case 'hello': {
      c.player.name = raw.name.slice(0, 16) || 'gjest';
      c.player.kind = clamp(raw.kind, 0, 5) as ChairKind;
      c.player.color = sanitiseColor(raw.color);
      send(c.ws, { t: 'welcome', id: c.player.id, players: snapshotPlayers(), phase });
      break;
    }
    case 'input': {
      c.player.x = raw.x; c.player.y = raw.y; c.player.z = raw.z;
      c.player.yaw = raw.yaw;
      c.lastInput = Date.now();
      break;
    }
    case 'ready': {
      c.player.ready = !!raw.ready;
      break;
    }
    case 'pickup': {
      if (phase.kind !== 'arena') break;
      const item = phase.data.pickups.find((p) => p.pid === raw.pid);
      if (!item || item.takenBy) break;
      const dx = c.player.x - item.x;
      const dz = c.player.z - item.z;
      if (dx * dx + dz * dz > PICKUP_RADIUS * PICKUP_RADIUS * 1.5) break;
      item.takenBy = c.player.id;
      const target = phase.data.targets[c.player.id];
      const ok = target ? matches(target, item) : false;
      // Stack always grows on a successful pickup. Score only increments on
      // a match — a wrong chair adds wasted weight without reward.
      if (ok) {
        c.player.score += 1;
        send(c.ws, { t: 'pickup-result', pid: item.pid, matched: true, chairId: item.chairId, glbPath: item.glbPath, reason: 'match' });
      } else {
        send(c.ws, {
          t: 'pickup-result', pid: item.pid, matched: false, chairId: item.chairId, glbPath: item.glbPath,
          reason: pickupReason(target, item),
        });
      }
      break;
    }
    case 'bump': {
      // intensity = collision relative speed in m/s. Walls and other players
      // both count. Drop K chairs based on intensity + current stack height
      // (taller stack falls more easily).
      if (Date.now() - c.lastBumpAt < 600) break;
      c.lastBumpAt = Date.now();
      if (c.player.score <= 0) break;
      const stack = c.player.score;
      // Each m/s above threshold knocks roughly one chair, capped by stack/3+1.
      const k = Math.min(stack, Math.max(1, Math.floor(raw.intensity / 4)));
      const cap = Math.max(1, Math.floor(stack / 3) + 1);
      const drop = Math.min(k, cap);
      c.player.score = Math.max(0, c.player.score - drop);
      break;
    }
  }
}

function clamp(n: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, n));
}

function sanitiseColor(c: string): string {
  return /^#[0-9A-Fa-f]{6}$/.test(c) ? c : '#B8542A';
}

const COLORS = ['#F0643B', '#24A6B8', '#F5BC42', '#9C58C7', '#49B86A', '#EF3F7A', '#FFD15C', '#5F8EE8'];

function newPlayer(): PlayerState {
  return {
    id: uid(),
    name: 'gjest',
    kind: 0,
    color: COLORS[conns.size % COLORS.length],
    x: (Math.random() - 0.5) * 6,
    y: 0.5,
    z: (Math.random() - 0.5) * 4,
    yaw: 0,
    score: 0,
    ready: false,
    alive: true,
  };
}

function respawnAll() {
  let i = 0;
  for (const c of conns.values()) {
    const spawn = stableSpawnPosition(i);
    c.player.x = spawn.x;
    c.player.y = spawn.y;
    c.player.z = spawn.z;
    c.player.yaw = spawn.yaw;
    i++;
  }
}

const wss = new WebSocketServer({ port: PORT });
console.log(`[stolspel] ws server on :${PORT}, ${CHAIRS.length} chairs in pool`);

wss.on('connection', (ws) => {
  const player = newPlayer();
  const c: Conn = { ws, player, lastInput: Date.now(), lastBumpAt: 0 };
  conns.set(player.id, c);
  console.log(`[+] ${player.id} connected, ${conns.size} total`);

  ws.on('message', (data) => {
    try {
      const msg = JSON.parse(data.toString()) as ClientMsg;
      handleMsg(c, msg);
    } catch (e) {
      console.warn('bad msg', e);
    }
  });

  ws.on('close', () => {
    conns.delete(player.id);
    console.log(`[-] ${player.id} left, ${conns.size} total`);
  });
});

setInterval(tick, TICK_MS);
