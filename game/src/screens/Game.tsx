import { useEffect, useMemo, useRef, useState } from 'react';
import { useGLTF } from '@react-three/drei';
import { World } from '../3d/World';
import { Hud } from './Hud';
import { TouchControls } from './TouchControls';
import type { NetApi } from '../net/useNet';
import type { StackedChair } from '../3d/ChairStack';

interface Props {
  net: NetApi;
}

interface PoolEntry { id: string; glbPath: string }

export function Game({ net }: Props) {
  const lastSent = useRef(0);
  const myXZ = useRef({ x: 0, z: 0 });
  const [, force] = useState(0);
  const [trippedAt, setTrippedAt] = useState(0);
  const me = net.players.find((p) => p.id === net.myId);
  const stack = useMemo<StackedChair[]>(() => me?.stack ?? [], [me?.stack]);

  // ── preload all chairs ────────────────────────────────────
  const [loaded, setLoaded] = useState(false);
  const [progress, setProgress] = useState(0);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch('/pbr_pool.json');
        if (!res.ok) throw new Error('failed to load pbr_pool');
        const pool = (await res.json()) as PoolEntry[];
        if (cancelled || !Array.isArray(pool)) return;
        setTotal(pool.length);
        let done = 0;
        // Sequential loading to prevent memory spikes
        for (const p of pool) {
          if (cancelled) break;
          try {
            await fetch(p.glbPath, { cache: 'force-cache' });
            await useGLTF.preload(p.glbPath);
          } catch (e) {
            console.warn(`[game] failed to preload ${p.id}:`, e);
          }
          done++;
          setProgress(done);
        }
        if (!cancelled) setTimeout(() => { if (!cancelled) setLoaded(true); }, 600);

      } catch (e) {
        console.error('[game] preload error:', e);
        if (!cancelled) setLoaded(true); // Proceed anyway to avoid permanent hang
      }
    })();
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    function onTrip(e: Event) {
      const d = (e as CustomEvent).detail as { victimId?: string; ts?: number };
      if (d?.victimId === net.myId) setTrippedAt(d.ts ?? Date.now());
    }
    window.addEventListener('stablar:trip', onTrip as EventListener);
    return () => window.removeEventListener('stablar:trip', onTrip as EventListener);
  }, [net.myId]);

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
          if (now - lastSent.current > 33) {
            lastSent.current = now;
            net.sendInput(x, y, z, yaw);
            force((n) => (n + 1) | 0);
          }
        }}
        onPickup={net.pickup}
        onBump={(otherId, intensity) => net.bump(otherId, intensity)}
      />
      <Hud
        phase={net.phase}
        players={net.players}
        myId={net.myId}
        onReady={net.ready}
      />
      <TouchControls phase={net.phase} />
      <TripFlash trippedAt={trippedAt} />
      {/* Preload fade overlay — fades out once chairs are loaded */}
      <div
        className="absolute inset-0 z-50 bg-bg flex items-center justify-center pointer-events-none transition-opacity duration-1000"
        style={{ opacity: loaded ? 0 : 1 }}
      >
        <div className="text-center">
          <div className="font-serif text-5xl text-paper mb-2">Stablar</div>
          <div className="font-mono text-[11px] uppercase tracking-[0.3em] text-inkSoft">
            lastar og lagrar stolar &nbsp;·&nbsp; {progress} / {total || '…'}
          </div>
          <div className="mt-6 font-mono text-[8px] uppercase tracking-widest text-inkSoft/40">
             stolar blir lagra lokalt for ein smidigare opplevelse
          </div>
        </div>
      </div>
    </div>
  );
}

function TripFlash({ trippedAt }: { trippedAt: number }) {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    if (!trippedAt) return;
    setVisible(true);
    const t = setTimeout(() => setVisible(false), 420);
    return () => clearTimeout(t);
  }, [trippedAt]);
  return (
    <div
      className="absolute inset-0 z-30 pointer-events-none transition-opacity duration-300"
      style={{
        opacity: visible ? 1 : 0,
        background: 'radial-gradient(circle at center, rgba(239,63,122,0.0) 30%, rgba(239,63,122,0.24) 100%)',
      }}
    >
      {visible && (
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 font-serif text-5xl text-rust select-none animate-bounce">
          fall!
        </div>
      )}
    </div>
  );
}
