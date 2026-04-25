import type {
  ClientMsg, ServerMsg, PlayerState, Phase, StableData, ChairKind,
  TargetRule, PickupItem,
} from '../../shared/protocol';
import { STABLE_ARENA, isInsideStableObstacle, stableSpawnPosition } from '../../shared/arena';

interface ChairRow {
  id: string; year: number; namn: string; stil: string;
  mat: string; nat: string | null;
  glbPath: string;
}

const TICK_MS = 50;
const PICKUP_RADIUS = 1.6;
const ARENA_HALF_X = STABLE_ARENA.halfX;
const ARENA_HALF_Z = STABLE_ARENA.halfZ;
const PICKUP_MIN_SPACING = 3.2;

const STIL_OPTIONS = ['Barokk', 'Rokokko', 'Nyklassisisme', 'Empire', 'Modernisme', 'Postmodernisme', 'Historisme'];
const NAT_OPTIONS = ['Noreg', 'Sverige', 'Danmark', 'Tyskland', 'England', 'Frankrike', 'Italia'];
const MAT_OPTIONS: Array<'tre' | 'metall' | 'plast' | 'lær' | 'tekstil'> = ['tre', 'metall', 'plast'];
const YEAR_BREAKS = [1700, 1800, 1850, 1900, 1950];

const COLORS = ['#F0643B', '#24A6B8', '#F5BC42', '#9C58C7', '#49B86A', '#EF3F7A', '#FFD15C', '#5F8EE8'];

export class LocalServer {
  private chairs: ChairRow[] = [];
  private conns = new Map<string, { player: PlayerState, lastBumpAt: number }>();
  private phase: Phase = { 
    kind: 'arena', 
    arenaIdx: 0, 
    arenaId: 'stable', 
    remainingMs: 0, 
    data: { targets: {}, pickups: [] } 
  };
  private onMessage: (msg: ServerMsg, toId?: string) => void;
  private interval: any;
  private rng = this.lcg(Date.now());

  constructor(onMessage: (msg: ServerMsg, toId?: string) => void) {
    this.onMessage = onMessage;
  }

  async start() {
    const res = await fetch('/pbr_pool.json');
    this.chairs = await res.json();
    this.populatePickups();
    this.interval = setInterval(() => this.tick(), TICK_MS);
  }

  stop() {
    clearInterval(this.interval);
  }

  addPlayer(id: string) {
    if (this.conns.has(id)) return;
    const player = this.newPlayer(id);
    this.conns.set(id, { player, lastBumpAt: 0 });
    if (this.phase.kind === 'arena') {
      this.phase.data.targets[id] = this.makeTarget(this.rng, new Set(), new Set());
    }
  }

  removePlayer(id: string) {
    this.conns.delete(id);
    if (this.phase.kind === 'arena') {
      delete this.phase.data.targets[id];
    }
  }

  handleClientMsg(id: string, raw: ClientMsg) {
    let c = this.conns.get(id);
    if (!c) {
      if (raw.t === 'hello') {
        this.addPlayer(id);
        c = this.conns.get(id)!;
      } else return;
    }

    switch (raw.t) {
      case 'hello': {
        c.player.name = raw.name.slice(0, 16) || 'gjest';
        c.player.kind = Math.max(0, Math.min(5, raw.kind)) as ChairKind;
        c.player.color = this.sanitiseColor(raw.color);
        this.onMessage({ t: 'welcome', id, players: this.snapshotPlayers(), phase: this.phase }, id);
        break;
      }
      case 'input': {
        c.player.x = raw.x; c.player.y = raw.y; c.player.z = raw.z;
        c.player.yaw = raw.yaw;
        break;
      }
      case 'pickup': {
        if (this.phase.kind !== 'arena') break;
        const itemIdx = this.phase.data.pickups.findIndex((p) => p.pid === raw.pid);
        const item = this.phase.data.pickups[itemIdx];
        if (!item || item.takenBy) break;

        const dx = c.player.x - item.x;
        const dz = c.player.z - item.z;
        if (dx * dx + dz * dz > PICKUP_RADIUS * PICKUP_RADIUS * 2.5) break;
        
        item.takenBy = c.player.id;
        const target = this.phase.data.targets[c.player.id];
        const ok = target ? this.matches(target, item as any) : false;
        
        if (ok) {
          c.player.score += 1;
          c.player.stack.push({ chairId: item.chairId, glbPath: item.glbPath });
          this.onMessage({ t: 'pickup-result', pid: item.pid, matched: true, chairId: item.chairId, glbPath: item.glbPath, reason: 'match' });
        } else {
          this.onMessage({
            t: 'pickup-result', pid: item.pid, matched: false, chairId: item.chairId, glbPath: item.glbPath,
            reason: this.pickupReason(target, item),
          });
        }

        setTimeout(() => {
          if (this.phase.kind === 'arena') {
            this.phase.data.pickups = this.phase.data.pickups.filter(p => p.pid !== raw.pid);
          }
        }, 50);
        break;
      }
      case 'bump': {
        const intensity = Number(raw.intensity);
        if (isNaN(intensity) || Date.now() - c.lastBumpAt < 600) break;
        c.lastBumpAt = Date.now();

        const otherConn = raw.otherId ? this.conns.get(raw.otherId) : null;
        const isPlayerHit = !!otherConn;

        const victims: Array<{ conn: typeof c; aggressor: typeof c | null }> = [];
        if (c.player.score > 0) victims.push({ conn: c, aggressor: otherConn ?? null });
        if (isPlayerHit && otherConn && otherConn.player.score > 0) {
          victims.push({ conn: otherConn, aggressor: c });
        }

        for (const v of victims) {
          const stackSize = v.conn.player.score;
          if (stackSize <= 0) continue;
          const dropMultiplier = isPlayerHit ? (stackSize > 4 ? 1.8 : 1.2) : 0.7;
          const k = Math.min(stackSize, Math.max(1, Math.floor((intensity * dropMultiplier) / 2.2)));
          const cap = Math.max(1, Math.floor(stackSize / 1.5) + 1);
          const drop = Math.min(k, cap);
          if (drop <= 0) continue;

          const dropped = v.conn.player.stack.slice(-drop);
          v.conn.player.score = Math.max(0, v.conn.player.score - drop);
          v.conn.player.stack = v.conn.player.stack.slice(0, v.conn.player.score);

          if (this.phase.kind === 'arena') {
            for (const item of dropped) {
              const angle = this.rng() * Math.PI * 2;
              const r = 1.2 + this.rng() * 1.4;
              const px = Math.max(-ARENA_HALF_X + 1, Math.min(ARENA_HALF_X - 1, v.conn.player.x + Math.cos(angle) * r));
              const pz = Math.max(-ARENA_HALF_Z + 1, Math.min(ARENA_HALF_Z - 1, v.conn.player.z + Math.sin(angle) * r));
              const chair = this.chairs.find((row) => row.id === item.chairId);
              this.phase.data.pickups.push({
                pid: `d${Date.now().toString(36)}${Math.random().toString(36).slice(2, 5)}`,
                chairId: item.chairId,
                glbPath: item.glbPath,
                year: chair?.year ?? 1900,
                mat: chair?.mat ?? 'tre',
                stil: chair?.stil ?? 'Modernisme',
                nat: chair?.nat ?? null,
                x: px,
                z: pz,
              });
            }
          }

          this.onMessage({
            t: 'trip',
            victimId: v.conn.player.id,
            victimName: v.conn.player.name,
            byId: v.aggressor?.player.id ?? null,
            byName: v.aggressor?.player.name ?? null,
            dropped: drop,
          });
        }
        break;
      }
    }
  }

  private tick() {
    if (this.phase.kind === 'arena') {
      this.spawnOnePickup();
    }
    let lightweightPhase = this.phase;
    if (this.phase.kind === 'arena') {
      lightweightPhase = { kind: 'arena', arenaIdx: this.phase.arenaIdx, arenaId: this.phase.arenaId, remainingMs: 0 } as any;
    }
    this.onMessage({ t: 'state', players: this.snapshotPlayers(), phase: lightweightPhase, ts: Date.now() });
  }

  private populatePickups() {
    if (this.phase.kind !== 'arena') return;
    for (let i = 0; i < this.chairs.length; i++) {
      this.spawnOnePickup();
    }
  }

  private spawnOnePickup() {
    if (this.phase.kind !== 'arena') return;
    const usedIds = new Set<string>();
    this.phase.data.pickups.forEach(p => usedIds.add(p.chairId));
    for (const c of this.conns.values()) {
      c.player.stack.forEach(s => usedIds.add(s.chairId));
    }
    const freeChairs = this.chairs.filter(c => !usedIds.has(c.id));
    if (freeChairs.length === 0) return;

    const chair = freeChairs[Math.floor(this.rng() * freeChairs.length)];
    const pos = this.placePickup(this.rng, this.phase.data.pickups);
    this.phase.data.pickups.push({
      pid: `p${Math.random().toString(36).slice(2, 7)}`,
      chairId: chair.id,
      glbPath: chair.glbPath,
      year: chair.year,
      mat: chair.mat,
      stil: chair.stil,
      nat: chair.nat,
      x: pos.x,
      z: pos.z,
    });
    this.onMessage({ t: 'phase', phase: this.phase });
  }

  private makeTarget(rng: () => number, takenStils: Set<string>, takenNats: Set<string>): TargetRule {
    const candidates: TargetRule[] = [];
    for (const y of YEAR_BREAKS) {
      candidates.push({ kind: 'before', year: y });
      candidates.push({ kind: 'after', year: y });
    }
    for (const m of MAT_OPTIONS) candidates.push({ kind: 'mat', mat: m });
    for (const s of STIL_OPTIONS) if (!takenStils.has(s)) candidates.push({ kind: 'stil', stil: s });
    for (const n of NAT_OPTIONS) if (!takenNats.has(n)) candidates.push({ kind: 'nat', nat: n });

    for (let i = candidates.length - 1; i > 0; i--) {
      const j = Math.floor(rng() * (i + 1));
      [candidates[i], candidates[j]] = [candidates[j], candidates[i]];
    }

    for (const t of candidates) {
      const n = this.chairs.filter((c) => this.matches(t, c)).length;
      if (n >= 2) return t;
    }
    return { kind: 'mat', mat: 'tre' };
  }

  private matches(target: TargetRule, c: ChairRow): boolean {
    switch (target.kind) {
      case 'before': return c.year < target.year;
      case 'after': return c.year > target.year;
      case 'between': return c.year >= target.from && c.year <= target.to;
      case 'mat': return c.mat.toLowerCase() === target.mat.toLowerCase();
      case 'stil': return c.stil.toLowerCase() === target.stil.toLowerCase();
      case 'nat': return (c.nat ?? '').toLowerCase() === target.nat.toLowerCase();
    }
  }

  private pickupReason(target: TargetRule | undefined, item: PickupItem): string {
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

  private lcg(seed: number): () => number {
    let s = seed >>> 0;
    return () => {
      s = (s * 1664525 + 1013904223) >>> 0;
      return s / 4294967296;
    };
  }

  private placePickup(rng: () => number, placed: PickupItem[]): { x: number; z: number } {
    const margin = STABLE_ARENA.pickupMargin;
    for (let attempt = 0; attempt < 80; attempt++) {
      const x = (rng() * 2 - 1) * (ARENA_HALF_X - margin);
      const z = (rng() * 2 - 1) * (ARENA_HALF_Z - margin);
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
      z: (rng() * 2 - 1) * (ARENA_HALF_Z - margin),
    };
  }

  private newPlayer(id: string): PlayerState {
    const spawn = stableSpawnPosition(this.conns.size);
    return {
      id, name: 'gjest', kind: 0, color: COLORS[this.conns.size % COLORS.length],
      x: spawn.x, y: spawn.y, z: spawn.z, yaw: spawn.yaw,
      score: 0, stack: [], ready: true, alive: true,
    };
  }

  private snapshotPlayers(): PlayerState[] {
    return [...this.conns.values()].map((c) => c.player);
  }

  private sanitiseColor(c: string): string {
    return /^#[0-9A-Fa-f]{6}$/.test(c) ? c : '#B8542A';
  }
}
