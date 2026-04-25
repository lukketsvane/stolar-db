import type { Phase, PlayerState, TargetRule } from '../../shared/protocol';

interface Props {
  phase: Phase;
  players: PlayerState[];
  myId: string | null;
  onReady: (r: boolean) => void;
}

export function Hud({ phase, players, myId, onReady }: Props) {
  const me = players.find((p) => p.id === myId);
  const myTarget: TargetRule | null = phase.kind === 'arena' && phase.arenaId === 'stable' && myId
    ? phase.data.targets[myId] ?? null
    : null;

  return (
    <>
      {/* top-left: room state */}
      <div className="absolute top-3 left-3 font-mono text-[11px] uppercase tracking-[0.18em] text-inkSoft select-none">
        STOLSPEL · {players.length} {players.length === 1 ? 'spelar' : 'spelarar'}
      </div>

      {/* top-right: phase / timer */}
      <div className="absolute top-3 right-3 font-mono text-[11px] uppercase tracking-[0.18em] text-inkSoft text-right select-none">
        {phaseLabel(phase)}
      </div>

      {/* leaderboard */}
      <div className="absolute top-12 right-3 w-56 select-none">
        {[...players].sort((a, b) => b.score - a.score).map((p) => (
          <div
            key={p.id}
            className={`flex items-center justify-between px-2 py-1 mb-0.5 font-mono text-[11px] border border-rule/70 shadow-sm ${
              p.id === myId ? 'bg-white text-paper' : 'bg-white/70 text-inkSoft'
            }`}
            style={{ borderLeft: `3px solid ${p.color}` }}
          >
            <span className="truncate flex-1">{p.name}{p.ready && ' ●'}</span>
            <span className="tabular-nums text-paper">{p.score}</span>
          </div>
        ))}
      </div>

      {/* big target display centered, during arena */}
      {phase.kind === 'arena' && myTarget && (
        <div className="absolute top-20 left-1/2 -translate-x-1/2 select-none pointer-events-none">
          <div className="card px-6 py-3 text-center bg-highlight/90 border-gold/30">
            <div className="font-serif text-3xl text-rust">{targetText(myTarget)}</div>
          </div>
        </div>
      )}

      {/* timer during arena — bottom-left */}
      {phase.kind === 'arena' && (
        <div className="absolute bottom-4 left-4 select-none pointer-events-none">
          <div className="font-mono text-4xl tabular-nums text-inkSoft drop-shadow-[0_1px_0_rgba(255,255,255,0.9)]">
            {Math.ceil(phase.remainingMs / 1000)}s
          </div>
        </div>
      )}

      {/* lobby controls */}
      {phase.kind === 'lobby' && me && (
        <div className="absolute bottom-8 inset-x-0 flex flex-col items-center gap-3 select-none">
          <button
            onClick={() => onReady(!me.ready)}
            className={`btn ${me.ready ? 'btn-primary' : 'btn-ghost'}`}
          >
            {me.ready ? 'Klar ●' : 'Trykk når klar'}
          </button>
        </div>
      )}

      {/* countdown — bottom-left */}
      {phase.kind === 'countdown' && (
        <div className="absolute bottom-4 left-4 select-none pointer-events-none">
          <div className="font-serif text-7xl text-paper drop-shadow-[0_2px_0_rgba(255,255,255,0.9)] tabular-nums">
            {Math.ceil(phase.remainingMs / 1000)}
          </div>
        </div>
      )}

      {/* results */}
      {phase.kind === 'results' && (
        <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
          <div className="card p-6 max-w-md w-full mx-4 pointer-events-auto bg-white/95">
            <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-inkSoft mb-2">
              resultat &mdash; runde {phase.arenaIdx + 1}
            </div>
            <div className="space-y-1.5">
              {phase.standings.map((s, i) => (
                <div key={s.id} className="flex items-baseline gap-3 font-mono text-sm">
                  <span className="w-6 text-inkSoft/70 tabular-nums">{i + 1}</span>
                  <span className="flex-1 text-paper truncate">{s.name}</span>
                  <span className="text-rust tabular-nums">+{s.delta}</span>
                  <span className="text-inkSoft tabular-nums w-12 text-right">{s.score}</span>
                </div>
              ))}
            </div>
            <div className="font-serif italic text-inkSoft text-sm mt-4">Tilbake til lobby snart.</div>
          </div>
        </div>
      )}
    </>
  );
}

function phaseLabel(p: Phase): string {
  switch (p.kind) {
    case 'lobby': return 'lobby';
    case 'countdown': return `start om ${Math.ceil(p.remainingMs / 1000)}…`;
    case 'arena': return 'STABLE-RUNDE';
    case 'results': return 'resultat';
  }
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
