import { useCallback, useEffect, useRef, useState } from 'react';
import { createClient, type RealtimeChannel } from '@supabase/supabase-js';
import type { ClientMsg, PlayerState, Phase, ChairKind, PickupItem, TargetRule } from '../../shared/protocol';
import { STABLE_ARENA, isInsideStableObstacle, stableSpawnPosition } from '../../shared/arena';

type PublicEnv = {
  VITE_SUPABASE_URL?: string;
  VITE_SUPABASE_ANON_KEY?: string;
  VITE_SUPABASE_PUBLISHABLE_KEY?: string;
  NEXT_PUBLIC_SUPABASE_URL?: string;
  NEXT_PUBLIC_SUPABASE_ANON_KEY?: string;
  NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY?: string;
};

const env = (import.meta as unknown as { env: PublicEnv }).env;
const SUPABASE_URL = env.VITE_SUPABASE_URL ?? env.NEXT_PUBLIC_SUPABASE_URL;
const SUPABASE_KEY =
  env.VITE_SUPABASE_ANON_KEY ??
  env.VITE_SUPABASE_PUBLISHABLE_KEY ??
  env.NEXT_PUBLIC_SUPABASE_ANON_KEY ??
  env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY;

const supabase = SUPABASE_URL && SUPABASE_KEY
  ? createClient(SUPABASE_URL, SUPABASE_KEY, {
      realtime: { params: { eventsPerSecond: 30 } },
    })
  : null;

export const COLORS = ['#F0643B', '#24A6B8', '#F5BC42', '#9C58C7', '#49B86A', '#EF3F7A', '#FFD15C', '#5F8EE8'];

interface NetState {
  connected: boolean;
  myId: string | null;
  players: PlayerState[];
  phase: Phase;
  ts: number;
  isHost: boolean;
  roomId: string | null;
}

export interface NetApi extends NetState {
  send: (msg: ClientMsg) => void;
  hello: (name: string, kind: ChairKind, color: string) => void;
  ready: (r: boolean) => void;
  sendInput: (x: number, y: number, z: number, yaw: number) => void;
  pickup: (pid: string) => void;
  bump: (otherId: string, intensity: number) => void;
}

interface ChairRow {
  id: string;
  namn?: string;
  glbPath: string;
  year?: number;
  mat?: string;
  stil?: string;
  nat?: string | null;
}

interface PlayerProfile {
  name: string;
  kind: ChairKind;
  color: string;
}

interface PresenceMeta {
  online_at?: string;
  profile?: PlayerProfile;
  player?: PlayerState;
}

type GameBroadcast =
  | { type: 'player'; senderId: string; player: PlayerState; sentAt: number }
  | { type: 'pickup'; senderId: string; pid: string; player: PlayerState; chairId: string; glbPath: string; sentAt: number }
  | { type: 'drop'; senderId: string; byId: string | null; byName: string | null; player: PlayerState; dropped: PickupItem[]; droppedCount: number; sentAt: number }
  | { type: 'sync-request'; senderId: string; sentAt: number }
  | { type: 'sync-state'; senderId: string; player: PlayerState; taken: string[]; dropped: PickupItem[]; sentAt: number };

const ID_KEY = 'stablar:client-id:v3';
const PROFILE_KEY = 'stablar:profile:v3';
const DEFAULT_ROOM = 'stabel-main';
const MOVE_SEND_MS = 58;
const MOVE_PUBLISH_MS = 110;
const TARGETS: TargetRule[] = [
  { kind: 'after', year: 1950 },
  { kind: 'before', year: 1900 },
  { kind: 'between', from: 1850, to: 1980 },
  { kind: 'mat', mat: 'tre' },
  { kind: 'stil', stil: 'Modernisme' },
  { kind: 'nat', nat: 'Noreg' },
];

const EMPTY_PHASE: Phase = {
  kind: 'arena',
  arenaIdx: 0,
  arenaId: 'stable',
  remainingMs: 0,
  data: { targets: {}, pickups: [] },
};

function hashString(value: string): number {
  let h = 2166136261;
  for (let i = 0; i < value.length; i++) {
    h ^= value.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

function rng(seed: number) {
  let t = seed >>> 0;
  return () => {
    t += 0x6D2B79F5;
    let x = Math.imul(t ^ (t >>> 15), 1 | t);
    x ^= x + Math.imul(x ^ (x >>> 7), 61 | x);
    return ((x ^ (x >>> 14)) >>> 0) / 4294967296;
  };
}

function createId(): string {
  const random = globalThis.crypto?.randomUUID?.() ?? Math.random().toString(36).slice(2);
  return `p-${random.replace(/-/g, '').slice(0, 10)}`;
}

function loadClientId(): string {
  try {
    const existing = localStorage.getItem(ID_KEY);
    if (existing) return existing;
    const next = createId();
    localStorage.setItem(ID_KEY, next);
    return next;
  } catch {
    return createId();
  }
}

function toChairKind(value: unknown, fallback: ChairKind): ChairKind {
  const n = Number(value);
  return Number.isInteger(n) && n >= 0 && n <= 5 ? n as ChairKind : fallback;
}

function defaultProfile(id: string): PlayerProfile {
  const h = hashString(id);
  return {
    name: `gjest ${10 + (h % 90)}`,
    kind: (h % 6) as ChairKind,
    color: COLORS[Math.floor((h / 7) % COLORS.length)] ?? COLORS[0],
  };
}

function loadProfile(id: string): PlayerProfile {
  const fallback = defaultProfile(id);
  try {
    const raw = localStorage.getItem(PROFILE_KEY);
    if (!raw) return fallback;
    const parsed = JSON.parse(raw) as Partial<PlayerProfile>;
    return {
      name: typeof parsed.name === 'string' && parsed.name.trim() ? parsed.name.trim().slice(0, 24) : fallback.name,
      kind: toChairKind(parsed.kind, fallback.kind),
      color: typeof parsed.color === 'string' && parsed.color ? parsed.color : fallback.color,
    };
  } catch {
    return fallback;
  }
}

function saveProfile(profile: PlayerProfile) {
  try {
    localStorage.setItem(PROFILE_KEY, JSON.stringify(profile));
  } catch {
    // localStorage can be unavailable in private contexts.
  }
}

function roomFromLocation(): string {
  const params = new URLSearchParams(window.location.search);
  const queryRoom = params.get('room');
  const hashRoom = window.location.hash.replace(/^#/, '');
  return (queryRoom || hashRoom || DEFAULT_ROOM).replace(/[^\w-]/g, '').slice(0, 48) || DEFAULT_ROOM;
}

function spawnFor(roomId: string, playerId: string) {
  return stableSpawnPosition(hashString(`${roomId}:${playerId}`) % 12);
}

function makePlayer(id: string, profile: PlayerProfile, roomId: string, current?: PlayerState): PlayerState {
  const spawn = current ? null : spawnFor(roomId, id);
  const stack = cleanStack(current?.stack);
  return {
    id,
    name: profile.name,
    kind: profile.kind,
    color: profile.color,
    x: current?.x ?? spawn?.x ?? 0,
    y: current?.y ?? spawn?.y ?? 1,
    z: current?.z ?? spawn?.z ?? STABLE_ARENA.spawnZ,
    yaw: current?.yaw ?? spawn?.yaw ?? Math.PI,
    score: stack.length,
    stack,
    ready: true,
    alive: true,
  };
}

function cleanStack(value: unknown): PlayerState['stack'] {
  if (!Array.isArray(value)) return [];
  return value
    .filter((item) => item && typeof item === 'object')
    .map((item) => item as { chairId?: unknown; glbPath?: unknown })
    .filter((item) => typeof item.chairId === 'string' && typeof item.glbPath === 'string')
    .map((item) => ({ chairId: item.chairId as string, glbPath: item.glbPath as string }))
    .slice(0, 40);
}

function finite(value: unknown, fallback: number): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function sanitizePlayer(raw: unknown, id: string, roomId: string): PlayerState {
  const fallbackProfile = defaultProfile(id);
  const base = makePlayer(id, fallbackProfile, roomId);
  if (!raw || typeof raw !== 'object') return base;
  const p = raw as Partial<PlayerState>;
  const stack = cleanStack(p.stack);
  return {
    id,
    name: typeof p.name === 'string' && p.name.trim() ? p.name.trim().slice(0, 24) : base.name,
    kind: toChairKind(p.kind, base.kind),
    color: typeof p.color === 'string' && p.color ? p.color : base.color,
    x: finite(p.x, base.x),
    y: finite(p.y, base.y),
    z: finite(p.z, base.z),
    yaw: finite(p.yaw, base.yaw),
    score: stack.length,
    stack,
    ready: true,
    alive: p.alive !== false,
  };
}

function rowToPickup(row: ChairRow, pid: string, x: number, z: number): PickupItem {
  return {
    pid,
    chairId: row.id,
    glbPath: row.glbPath,
    year: Number.isFinite(Number(row.year)) ? Number(row.year) : 1950,
    mat: typeof row.mat === 'string' && row.mat ? row.mat : 'tre',
    stil: typeof row.stil === 'string' && row.stil ? row.stil : 'Samtidsdesign',
    nat: typeof row.nat === 'string' ? row.nat : null,
    x,
    z,
  };
}

function buildPickups(pool: ChairRow[], roomId: string): PickupItem[] {
  const rows = pool.filter((p) => p && typeof p.id === 'string' && typeof p.glbPath === 'string' && p.glbPath);
  if (!rows.length) return [];
  const random = rng(hashString(`pickups:${roomId}:v5`));
  const count = Math.min(32, Math.max(24, rows.length * 2));
  const pickups: PickupItem[] = [];
  let attempts = 0;

  while (pickups.length < count && attempts < 4000) {
    attempts++;
    const x = -STABLE_ARENA.halfX + STABLE_ARENA.pickupMargin + random() * ((STABLE_ARENA.halfX - STABLE_ARENA.pickupMargin) * 2);
    const z = -STABLE_ARENA.halfZ + STABLE_ARENA.pickupMargin + random() * ((STABLE_ARENA.halfZ - STABLE_ARENA.pickupMargin) * 2);
    const awayFromSpawn = z < STABLE_ARENA.spawnZ - 6;
    if (!awayFromSpawn) continue;
    if (isInsideStableObstacle(x, z, 2.7)) continue;
    if (pickups.some((p) => Math.hypot(p.x - x, p.z - z) < 4.0)) continue;

    const row = rows[Math.floor(random() * rows.length)] ?? rows[pickups.length % rows.length];
    pickups.push(rowToPickup(row, `${roomId}-pickup-${pickups.length}`, Number(x.toFixed(2)), Number(z.toFixed(2))));
  }

  return pickups;
}

function targetFor(playerId: string): TargetRule {
  return TARGETS[hashString(`target:${playerId}`) % TARGETS.length] ?? TARGETS[0];
}

function sortPlayers(players: PlayerState[]): PlayerState[] {
  return [...players].sort((a, b) => b.score - a.score || a.name.localeCompare(b.name) || a.id.localeCompare(b.id));
}

function uniqueDropped(items: PickupItem[]): PickupItem[] {
  const seen = new Set<string>();
  const next: PickupItem[] = [];
  for (const item of items) {
    if (seen.has(item.pid)) continue;
    seen.add(item.pid);
    next.push(item);
  }
  return next.slice(-80);
}

function pickupKeyToRow(stackItem: { chairId: string; glbPath: string }, poolById: Map<string, ChairRow>): ChairRow {
  const row = poolById.get(stackItem.chairId);
  if (row) return row;
  return {
    id: stackItem.chairId,
    glbPath: stackItem.glbPath,
    year: 1950,
    mat: 'tre',
    stil: 'Samtidsdesign',
    nat: null,
  };
}

export function useNet(): NetApi {
  const channelRef = useRef<RealtimeChannel | null>(null);
  const subscribedRef = useRef(false);
  const myIdRef = useRef<string | null>(null);
  const roomIdRef = useRef<string | null>(null);
  const profileRef = useRef<PlayerProfile | null>(null);
  const selfRef = useRef<PlayerState | null>(null);
  const remotesRef = useRef(new Map<string, PlayerState>());
  const onlineRef = useRef(new Set<string>());
  const basePickupsRef = useRef<PickupItem[]>([]);
  const droppedPickupsRef = useRef<PickupItem[]>([]);
  const takenRef = useRef(new Set<string>());
  const poolByIdRef = useRef(new Map<string, ChairRow>());
  const lastMoveSentRef = useRef(0);
  const lastMovePublishRef = useRef(0);

  const [state, setState] = useState<NetState>({
    connected: false,
    myId: null,
    players: [],
    phase: EMPTY_PHASE,
    ts: 0,
    isHost: false,
    roomId: null,
  });

  const buildPhase = useCallback((players: PlayerState[]): Phase => {
    const targets: Record<string, TargetRule> = {};
    for (const player of players) targets[player.id] = targetFor(player.id);
    const allPickups = [...basePickupsRef.current, ...droppedPickupsRef.current];
    const pickups = allPickups
      .filter((item) => !takenRef.current.has(item.pid))
      .map((item) => ({ ...item }));
    return {
      kind: 'arena',
      arenaIdx: 0,
      arenaId: 'stable',
      remainingMs: 0,
      data: { targets, pickups },
    };
  }, []);

  const publish = useCallback((connected?: boolean) => {
    const myId = myIdRef.current;
    const roomId = roomIdRef.current;
    const players: PlayerState[] = [];
    if (selfRef.current) players.push(selfRef.current);
    for (const [id, player] of remotesRef.current) {
      if (!onlineRef.current.size || onlineRef.current.has(id)) players.push(player);
    }
    const sorted = sortPlayers(players);
    setState((cur) => ({
      connected: connected ?? cur.connected,
      myId,
      players: sorted,
      phase: buildPhase(sorted),
      ts: Date.now(),
      isHost: false,
      roomId,
    }));
  }, [buildPhase]);

  const sendRealtime = useCallback((payload: GameBroadcast) => {
    const channel = channelRef.current;
    if (!channel || !subscribedRef.current) return;
    void channel.send({ type: 'broadcast', event: 'game', payload });
  }, []);

  const trackSelf = useCallback(() => {
    const channel = channelRef.current;
    const profile = profileRef.current;
    const player = selfRef.current;
    if (!channel || !subscribedRef.current || !profile || !player) return;
    void channel.track({
      online_at: new Date().toISOString(),
      profile,
      player,
    });
  }, []);

  const handleBroadcast = useCallback((payload: GameBroadcast) => {
    const myId = myIdRef.current;
    const roomId = roomIdRef.current ?? DEFAULT_ROOM;
    if (!payload || payload.senderId === myId) return;

    if (payload.type === 'player') {
      remotesRef.current.set(payload.senderId, sanitizePlayer(payload.player, payload.senderId, roomId));
      publish(true);
      return;
    }

    if (payload.type === 'pickup') {
      takenRef.current.add(payload.pid);
      remotesRef.current.set(payload.senderId, sanitizePlayer(payload.player, payload.senderId, roomId));
      publish(true);
      return;
    }

    if (payload.type === 'drop') {
      remotesRef.current.set(payload.senderId, sanitizePlayer(payload.player, payload.senderId, roomId));
      droppedPickupsRef.current = uniqueDropped([...droppedPickupsRef.current, ...payload.dropped]);
      window.dispatchEvent(new CustomEvent('stablar:trip', {
        detail: {
          victimId: payload.senderId,
          victimName: payload.player.name,
          byId: payload.byId,
          byName: payload.byName,
          dropped: payload.droppedCount,
          ts: Date.now(),
        },
      }));
      publish(true);
      return;
    }

    if (payload.type === 'sync-request') {
      const self = selfRef.current;
      if (!self || !myId) return;
      sendRealtime({
        type: 'sync-state',
        senderId: myId,
        player: self,
        taken: [...takenRef.current],
        dropped: droppedPickupsRef.current,
        sentAt: Date.now(),
      });
      return;
    }

    if (payload.type === 'sync-state') {
      remotesRef.current.set(payload.senderId, sanitizePlayer(payload.player, payload.senderId, roomId));
      for (const pid of payload.taken) takenRef.current.add(pid);
      droppedPickupsRef.current = uniqueDropped([...droppedPickupsRef.current, ...payload.dropped]);
      publish(true);
    }
  }, [publish, sendRealtime]);

  useEffect(() => {
    let cancelled = false;
    const myId = loadClientId();
    const roomId = roomFromLocation();
    const profile = loadProfile(myId);
    myIdRef.current = myId;
    roomIdRef.current = roomId;
    profileRef.current = profile;
    selfRef.current = makePlayer(myId, profile, roomId);
    onlineRef.current = new Set([myId]);
    publish(false);

    fetch('/pbr_pool.json', { cache: 'force-cache' })
      .then((res) => res.ok ? res.json() : [])
      .then((pool: ChairRow[]) => {
        if (cancelled || !Array.isArray(pool)) return;
        poolByIdRef.current = new Map(pool.map((row) => [row.id, row]));
        basePickupsRef.current = buildPickups(pool, roomId);
        publish(subscribedRef.current || !supabase);
      })
      .catch(() => {
        if (!cancelled) publish(subscribedRef.current || !supabase);
      });

    if (!supabase) {
      publish(true);
      return () => { cancelled = true; };
    }

    const channel = supabase.channel(`stablar:${roomId}`, {
      config: {
        presence: { key: myId },
        broadcast: { self: false, ack: false },
      },
    });
    channelRef.current = channel;

    channel.on('broadcast', { event: 'game' }, ({ payload }) => {
      if (!cancelled) handleBroadcast(payload as GameBroadcast);
    });

    channel.on('presence', { event: 'sync' }, () => {
      if (cancelled) return;
      const presence = channel.presenceState() as Record<string, PresenceMeta[]>;
      const online = new Set<string>([myId]);
      for (const [id, metas] of Object.entries(presence)) {
        online.add(id);
        if (id === myId) continue;
        const meta = metas[metas.length - 1] ?? {};
        if (!remotesRef.current.has(id)) {
          if (meta.player) remotesRef.current.set(id, sanitizePlayer(meta.player, id, roomId));
          else remotesRef.current.set(id, makePlayer(id, meta.profile ?? defaultProfile(id), roomId));
        }
      }
      for (const id of [...remotesRef.current.keys()]) {
        if (!online.has(id)) remotesRef.current.delete(id);
      }
      onlineRef.current = online;
      publish(true);
    });

    channel.subscribe((status) => {
      if (cancelled) return;
      if (status === 'SUBSCRIBED') {
        subscribedRef.current = true;
        trackSelf();
        sendRealtime({ type: 'sync-request', senderId: myId, sentAt: Date.now() });
        publish(true);
      }
      if (status === 'CHANNEL_ERROR' || status === 'TIMED_OUT' || status === 'CLOSED') {
        subscribedRef.current = false;
        publish(false);
      }
    });

    return () => {
      cancelled = true;
      subscribedRef.current = false;
      void channel.unsubscribe();
      channelRef.current = null;
    };
  }, [handleBroadcast, publish, sendRealtime, trackSelf]);

  const updateSelf = useCallback((mutate: (player: PlayerState) => PlayerState, immediate = false) => {
    const current = selfRef.current;
    if (!current) return null;
    const next = mutate(current);
    selfRef.current = { ...next, score: cleanStack(next.stack).length, stack: cleanStack(next.stack), ready: true, alive: true };
    if (immediate) publish(true);
    return selfRef.current;
  }, [publish]);

  const hello = useCallback((name: string, kind: ChairKind, color: string) => {
    const profile: PlayerProfile = {
      name: name.trim().slice(0, 24) || profileRef.current?.name || 'gjest',
      kind: toChairKind(kind, profileRef.current?.kind ?? 0),
      color: color || profileRef.current?.color || COLORS[0],
    };
    profileRef.current = profile;
    saveProfile(profile);
    const self = updateSelf((p) => ({ ...p, name: profile.name, kind: profile.kind, color: profile.color }), true);
    trackSelf();
    if (self && myIdRef.current) sendRealtime({ type: 'player', senderId: myIdRef.current, player: self, sentAt: Date.now() });
  }, [sendRealtime, trackSelf, updateSelf]);

  const ready = useCallback((readyValue: boolean) => {
    const self = updateSelf((p) => ({ ...p, ready: readyValue }), true);
    if (self && myIdRef.current) sendRealtime({ type: 'player', senderId: myIdRef.current, player: self, sentAt: Date.now() });
  }, [sendRealtime, updateSelf]);

  const sendInput = useCallback((x: number, y: number, z: number, yaw: number) => {
    if (![x, y, z, yaw].every(Number.isFinite)) return;
    const now = performance.now();
    const self = updateSelf((p) => ({ ...p, x, y, z, yaw }), now - lastMovePublishRef.current > MOVE_PUBLISH_MS);
    if (!self || !myIdRef.current) return;
    if (now - lastMovePublishRef.current > MOVE_PUBLISH_MS) lastMovePublishRef.current = now;
    if (now - lastMoveSentRef.current > MOVE_SEND_MS) {
      lastMoveSentRef.current = now;
      sendRealtime({ type: 'player', senderId: myIdRef.current, player: self, sentAt: Date.now() });
    }
  }, [sendRealtime, updateSelf]);

  const pickup = useCallback((pid: string) => {
    if (!pid || takenRef.current.has(pid)) return;
    const item = [...basePickupsRef.current, ...droppedPickupsRef.current].find((p) => p.pid === pid);
    if (!item) return;
    takenRef.current.add(pid);
    const self = updateSelf((p) => ({
      ...p,
      stack: [...p.stack, { chairId: item.chairId, glbPath: item.glbPath }],
    }), true);
    if (!self || !myIdRef.current) return;
    window.dispatchEvent(new CustomEvent('stablar:pickup-result', {
      detail: { matched: true, reason: 'samla', chairId: item.chairId, glbPath: item.glbPath, ts: Date.now() },
    }));
    sendRealtime({
      type: 'pickup',
      senderId: myIdRef.current,
      pid,
      chairId: item.chairId,
      glbPath: item.glbPath,
      player: self,
      sentAt: Date.now(),
    });
  }, [sendRealtime, updateSelf]);

  const bump = useCallback((otherId: string, intensity: number) => {
    const self = selfRef.current;
    const myId = myIdRef.current;
    if (!self || !myId || self.stack.length === 0) return;
    const count = Math.max(1, Math.min(self.stack.length, Math.ceil(Math.max(0, intensity - 4) / 4)));
    const fallen = self.stack.slice(-count);
    const kept = self.stack.slice(0, -count);
    const by = otherId ? remotesRef.current.get(otherId) : null;
    const now = Date.now();
    const dropped = fallen.map((stackItem, i) => {
      const angle = self.yaw + Math.PI + (i - (fallen.length - 1) / 2) * 0.55;
      const dist = 1.6 + i * 0.45;
      const x = Math.max(-STABLE_ARENA.halfX + 2, Math.min(STABLE_ARENA.halfX - 2, self.x + Math.sin(angle) * dist));
      const z = Math.max(-STABLE_ARENA.halfZ + 2, Math.min(STABLE_ARENA.halfZ - 2, self.z + Math.cos(angle) * dist));
      const row = pickupKeyToRow(stackItem, poolByIdRef.current);
      return {
        ...rowToPickup(row, `drop-${myId}-${now}-${i}`, Number(x.toFixed(2)), Number(z.toFixed(2))),
        droppedAt: now,
        availableAt: now + 1200,
        dropYaw: angle,
      };
    });

    droppedPickupsRef.current = uniqueDropped([...droppedPickupsRef.current, ...dropped]);
    const next = updateSelf((p) => ({ ...p, stack: kept }), true);
    if (!next) return;
    window.dispatchEvent(new CustomEvent('stablar:trip', {
      detail: {
        victimId: myId,
        victimName: next.name,
        byId: by?.id ?? null,
        byName: by?.name ?? null,
        dropped: count,
        ts: Date.now(),
      },
    }));
    sendRealtime({
      type: 'drop',
      senderId: myId,
      byId: by?.id ?? null,
      byName: by?.name ?? null,
      player: next,
      dropped,
      droppedCount: count,
      sentAt: Date.now(),
    });
  }, [sendRealtime, updateSelf]);

  const send = useCallback((msg: ClientMsg) => {
    if (msg.t === 'hello') hello(msg.name, msg.kind, msg.color);
    if (msg.t === 'ready') ready(msg.ready);
    if (msg.t === 'input') sendInput(msg.x, msg.y, msg.z, msg.yaw);
    if (msg.t === 'pickup') pickup(msg.pid);
    if (msg.t === 'bump') bump(msg.otherId, msg.intensity);
  }, [bump, hello, pickup, ready, sendInput]);

  return { ...state, send, hello, ready, sendInput, pickup, bump };
}
