import { useEffect, useRef, useState } from 'react';
import { useGLTF } from '@react-three/drei';
import { World } from '../3d/World';
import { Hud } from './Hud';
import { TouchControls } from './TouchControls';
import type { NetApi } from '../net/useNet';
import type { StackedChair } from '../3d/ChairStack';

interface Props {
  net: NetApi;
}

interface PickupFeedback {
  matched: boolean;
  reason: string;
  chairId: string;
  glbPath: string;
  ts: number;
}

interface PoolEntry { id: string; glbPath: string }

export function Game({ net }: Props) {
  const lastSent = useRef(0);
  const myXZ = useRef({ x: 0, z: 0 });
  const [, force] = useState(0);
  const [stack, setStack] = useState<StackedChair[]>([]);
  const lastSeenScore = useRef(0);

  // ── preload all chairs ────────────────────────────────────
  const [loaded, setLoaded] = useState(false);
  const [progress, setProgress] = useState(0);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      const res = await fetch('/pbr_pool.json');
      const pool = (await res.json()) as PoolEntry[];
      if (cancelled) return;
      setTotal(pool.length);
      let done = 0;
      await Promise.all(pool.map(async (p) => {
        try {
          await fetch(p.glbPath, { cache: 'force-cache' });
          useGLTF.preload(p.glbPath);
        } catch {/* ignore */}
        done++;
        if (!cancelled) setProgress(done);
      }));
      if (!cancelled) setTimeout(() => { if (!cancelled) setLoaded(true); }, 600);
    })();
    return () => { cancelled = true; };
  }, []);

  // ── pickup feedback / local stack ─────────────────────────
  useEffect(() => {
    function onPickupResult(e: Event) {
      const d = (e as CustomEvent).detail as PickupFeedback;
      setStack((prev) => [...prev, { chairId: d.chairId, glbPath: d.glbPath }]);
    }
    window.addEventListener('stolspel:pickup-result', onPickupResult as EventListener);
    return () => window.removeEventListener('stolspel:pickup-result', onPickupResult as EventListener);
  }, []);

  useEffect(() => {
    const me = net.players.find((p) => p.id === net.myId);
    if (!me) return;
    if (me.score < lastSeenScore.current) {
      const drop = lastSeenScore.current - me.score;
      setStack((prev) => prev.slice(0, Math.max(0, prev.length - drop)));
    }
    lastSeenScore.current = me.score;
  }, [net.players, net.myId]);

  useEffect(() => {
    if (net.phase.kind === 'lobby' || net.phase.kind === 'countdown') {
      setStack([]);
      lastSeenScore.current = 0;
    }
  }, [net.phase.kind]);

  return (
    <div className="relative w-screen h-screen bg-bg overflow-hidden">
      <World
        myId={net.myId}
        players={net.players}
        phase={net.phase}
        myX={myXZ.current.x}
        myZ={myXZ.current.z}
        stackedChairs={stack}
        onTransform={(x, y, z, yaw) => {
          myXZ.current = { x, z };
          const now = performance.now();
          if (now - lastSent.current > 50) {
            lastSent.current = now;
            net.sendInput(x, y, z, yaw);
            force((n) => (n + 1) | 0);
          }
        }}
        onPickup={net.pickup}
        onBump={(intensity) => net.bump('', intensity)}
      />
      <Hud
        phase={net.phase}
        players={net.players}
        myId={net.myId}
        onReady={net.ready}
      />
      <TouchControls phase={net.phase} />
      {/* Preload fade overlay — fades out once chairs are loaded */}
      <div
        className="absolute inset-0 z-50 bg-bg flex items-center justify-center pointer-events-none transition-opacity duration-1000"
        style={{ opacity: loaded ? 0 : 1 }}
      >
        <div className="text-center">
          <div className="font-serif text-5xl text-paper mb-2">Stolspel</div>
          <div className="font-mono text-[11px] uppercase tracking-[0.3em] text-inkSoft">
            lastar stolar &nbsp;·&nbsp; {progress} / {total || '…'}
          </div>
        </div>
      </div>
    </div>
  );
}
