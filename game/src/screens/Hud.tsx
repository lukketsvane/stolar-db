import { useEffect, useState, useMemo } from 'react';
import type { Phase, PlayerState, TargetRule } from '../../shared/protocol';

interface Props {
  phase: Phase;
  players: PlayerState[];
  myId: string | null;
  onReady: (r: boolean) => void;
}

interface TripEvent {
  victimId: string;
  victimName: string;
  byId: string | null;
  byName: string | null;
  dropped: number;
  ts: number;
}

export function Hud({ phase, players = [], myId }: Props) {
  const [achievement, setAchievement] = useState("");
  const [tripBanner, setTripBanner] = useState<TripEvent | null>(null);
  const me = players.find((p) => p.id === myId);

  useEffect(() => {
    function onTrip(e: Event) {
      const d = (e as CustomEvent).detail as TripEvent;
      if (!d) return;
      setTripBanner(d);
      const id = setTimeout(() => setTripBanner((cur) => (cur && cur.ts === d.ts ? null : cur)), 2400);
      return () => clearTimeout(id);
    }
    window.addEventListener('stablar:trip', onTrip as EventListener);
    return () => window.removeEventListener('stablar:trip', onTrip as EventListener);
  }, []);
  
  const myTarget: TargetRule | null = (phase && phase.kind === 'arena' && phase.arenaId === 'stable' && myId && phase.data)
    ? phase.data.targets[myId] ?? null
    : null;

  // Achievement logic — keyword-based, robust against new chair ids
  const stats = useMemo(() => {
    if (!me || !me.stack) return null;
    const ids = me.stack.map(s => s.chairId.toLowerCase());
    const all = ids.length;

    const wooden = ids.filter(id => id.includes('wood') || id.includes('tre') || id.includes('heltre') || id.startsWith('c0') || id.startsWith('c1')).length;
    const rocking = ids.filter(id => id.includes('rocking') || id.includes('gynge')).length;
    const baroque = ids.filter(id => id.includes('baroque') || id.includes('antique') || id.includes('throne') || id.includes('ornate')).length;
    const modern = ids.filter(id => id.includes('modern') || id.includes('ergonomic') || id.includes('office') || id.includes('plastic')).length;

    if (all >= 9) return `Episk stabel (${all}) — ikkje fall!`;
    if (all >= 6) return `Legendarisk stabel (${all})`;
    if (rocking >= 2) return `Gyngestol-meister (${rocking})`;
    if (baroque >= 3) return `Barokk-samlar (${baroque})`;
    if (modern >= 3) return `Modernist (${modern})`;
    if (wooden >= 4) return `${wooden} trestolar samla`;
    if (all >= 3) return `${all} stolar — gå vidare`;
    if (all >= 1) return `${all} stolar i stabelen`;
    return "";
  }, [me?.stack]);

  useEffect(() => {
    if (stats) setAchievement(stats);
  }, [stats]);

  if (!phase) return null;

  return (
    <div className="transition-opacity">
      {/* top-center: dynamic achievement / typewriter */}
      {achievement && (
        <div className="absolute top-6 left-1/2 -translate-x-1/2 z-20 pointer-events-none">
          <div className="font-mono text-sm uppercase tracking-[0.3em] text-paper/80 animate-pulse bg-white/40 px-4 py-1 backdrop-blur-sm border-b border-rule/50">
            {achievement}
          </div>
        </div>
      )}

      {/* trip banner */}
      {tripBanner && (
        <div key={tripBanner.ts} className="absolute top-16 left-1/2 -translate-x-1/2 z-30 pointer-events-none">
          <div className="font-serif text-2xl text-rust bg-highlight/95 px-5 py-2 border-2 border-rust/40 whitespace-nowrap">
            {tripBanner.byName
              ? <><span className="font-bold">{tripBanner.byName}</span> felte <span className="font-bold">{tripBanner.victimName}</span> · {tripBanner.dropped} fall</>
              : <><span className="font-bold">{tripBanner.victimName}</span> snubla · {tripBanner.dropped} fall</>
            }
          </div>
        </div>
      )}

      {/* top-left: room state */}
      <div className="absolute top-3 left-3 font-mono text-[11px] uppercase tracking-[0.18em] text-inkSoft select-none">
        STABLAR · {players.length} {players.length === 1 ? 'spelar' : 'spelarar'}
      </div>

      {/* leaderboard */}
      <div className="absolute top-3 right-3 w-56 select-none">
        <div className="mb-4">
           <div className="font-mono text-[10px] uppercase tracking-[0.2em] text-[#5F8EE8] mb-1.5">Noverande</div>
           {[...players].filter(p => p && typeof p.score === 'number').sort((a, b) => b.score - a.score).map((p) => (
             <div
               key={p.id}
               className={`flex items-center justify-between px-2 py-1 mb-0.5 font-mono text-[11px] border border-rule/70 ${
                 p.id === myId ? 'bg-white text-paper' : 'bg-white/70 text-inkSoft'
               }`}
               style={{ borderLeft: `3px solid ${p.color}` }}
             >
               <span className="truncate flex-1">{p.name}</span>
               <span className="tabular-nums text-paper">{p.score}</span>
             </div>
           ))}
        </div>

      </div>

      {/* big target display centered */}
      {phase.kind === 'arena' && myTarget && (
        <div className="absolute top-20 left-1/2 -translate-x-1/2 select-none pointer-events-none">
          <div className="card px-6 py-3 text-center bg-highlight/90 border-gold/30">
            <div className="font-serif text-3xl text-rust">{targetText(myTarget)}</div>
          </div>
        </div>
      )}
    </div>
  );
}

function targetText(t: TargetRule): string {
  switch (t.kind) {
    case 'before': return `stolar frå før ${t.year}`;
    case 'after': return `stolar etter ${t.year}`;
    case 'between': return `stolar frå ${t.from}–${t.to}`;
    case 'mat': return `stolar i ${matNynorsk(t.mat)}`;
    case 'stil': return `${t.stil}-stolar`;
    case 'nat': return `stolar frå ${t.nat}`;
  }
}

function matNynorsk(m: string): string {
  switch (m) {
    case 'tre': return 'tre';
    case 'metall': return 'metall';
    case 'plast': return 'plast';
    case 'lær': return 'lær';
    case 'tekstil': return 'tekstil';
    default: return m;
  }
}
