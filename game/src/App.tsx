import { useEffect, useState } from 'react';
import { useNet } from './net/useNet';
import { PreGameLobby } from './screens/PreGameLobby';
import { Game } from './screens/Game';
import { loadChairs } from './data/chairs';
import type { ChairKind } from '../shared/protocol';

export function App() {
  const net = useNet();
  const [joined, setJoined] = useState(false);
  const [chairsReady, setChairsReady] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    loadChairs().then(() => setChairsReady(true)).catch((e) => setErr(String(e)));
  }, []);

  // Submit to game on Enter when in arena
  useEffect(() => {
    if (net.phase.kind !== 'arena') return;
    function onKey(e: KeyboardEvent) {
      if (e.code === 'Enter') {
        // We can't read x here; HUD button does the actual submit.
        // (Hud already reads myX.)
      }
    }
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [net.phase]);

  if (err) return <div className="p-10 font-mono text-rust">FEIL: {err}</div>;

  if (!net.connected) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-paper/50 animate-pulse">
          koblar til serveren …
        </div>
      </div>
    );
  }

  if (!joined || !net.myId) {
    return (
      <PreGameLobby
        onJoin={(name, kind, color) => {
          net.hello(name, kind as ChairKind, color);
          setJoined(true);
        }}
      />
    );
  }

  if (!chairsReady) {
    return <div className="p-10 font-mono text-paper/50">lastar stolar …</div>;
  }

  return <Game net={net} />;
}
