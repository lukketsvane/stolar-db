import { useCallback, useEffect, useRef, useState } from 'react';
import type { Phase } from '../../shared/protocol';

interface Props {
  phase: Phase;
}

interface TouchState {
  x: number;
  y: number;
  jump: boolean;
  sprint: boolean;
}

const ZERO: TouchState = { x: 0, y: 0, jump: false, sprint: false };
const STICK_RADIUS = 135;

export function TouchControls({ phase }: Props) {
  const active = phase.kind === 'arena' || phase.kind === 'countdown';
  const [enabled, setEnabled] = useState(false);
  const [hasInteracted, setHasInteracted] = useState(() => localStorage.getItem('stablar:controls-seen') === 'true');
  const [state, setState] = useState<TouchState>(ZERO);
  const stickRef = useRef<HTMLDivElement>(null);
  const pointerId = useRef<number | null>(null);
  const latest = useRef<TouchState>(ZERO);

  useEffect(() => {
    const query = window.matchMedia('(pointer: coarse)');
    const update = () => setEnabled(query.matches);
    update();
    query.addEventListener('change', update);
    return () => query.removeEventListener('change', update);
  }, []);

  const emit = useCallback((next: TouchState) => {
    latest.current = next;
    setState(next);
    window.dispatchEvent(new CustomEvent('stablar:touch-input', { detail: next }));
    
    if (!hasInteracted && (Math.abs(next.x) > 0.1 || Math.abs(next.y) > 0.1 || next.jump)) {
      setHasInteracted(true);
      localStorage.setItem('stablar:controls-seen', 'true');
    }
  }, [hasInteracted]);

  useEffect(() => {
    if (!active) emit(ZERO);
  }, [active, emit]);

  useEffect(() => {
    const stop = () => emit(ZERO);
    window.addEventListener('blur', stop);
    return () => {
      stop();
      window.removeEventListener('blur', stop);
    };
  }, [emit]);

  if (!enabled || !active) return null;

  const setStickFromPointer = (clientX: number, clientY: number) => {
    const rect = stickRef.current?.getBoundingClientRect();
    if (!rect) return;
    const cx = rect.left + rect.width / 2;
    const cy = rect.top + rect.height / 2;
    const rawX = clientX - cx;
    const rawY = clientY - cy;
    const len = Math.hypot(rawX, rawY);
    const scale = len > STICK_RADIUS ? STICK_RADIUS / len : 1;
    emit({
      ...latest.current,
      x: (rawX * scale) / STICK_RADIUS,
      y: (rawY * scale) / STICK_RADIUS,
    });
  };

  const setButton = (key: 'jump' | 'sprint', value: boolean) => {
    emit({ ...latest.current, [key]: value });
  };

  return (
    <div
      data-touch-controls="true"
      className={`absolute inset-x-0 bottom-0 z-40 flex items-end justify-between px-6 pb-12 pointer-events-none select-none md:hidden transition-opacity duration-1000 ${hasInteracted ? 'opacity-[0.03]' : 'opacity-40'}`}
    >
      <div
        ref={stickRef}
        className="relative h-[300px] w-[300px] rounded-full border-2 border-ink bg-white/20 pointer-events-auto touch-none"
        onPointerDown={(e) => {
          pointerId.current = e.pointerId;
          e.currentTarget.setPointerCapture(e.pointerId);
          setStickFromPointer(e.clientX, e.clientY);
        }}
        onPointerMove={(e) => {
          if (pointerId.current === e.pointerId) setStickFromPointer(e.clientX, e.clientY);
        }}
        onPointerUp={(e) => {
          if (pointerId.current !== e.pointerId) return;
          pointerId.current = null;
          emit({ ...latest.current, x: 0, y: 0 });
        }}
        onPointerCancel={() => {
          pointerId.current = null;
          emit({ ...latest.current, x: 0, y: 0 });
        }}
      >
        <div className="absolute inset-[60px] rounded-full border border-ink/20" />
        <div
          className="absolute left-1/2 top-1/2 h-[100px] w-[100px] -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-ink bg-ink/10"
          style={{ transform: `translate(calc(-50% + ${state.x * STICK_RADIUS}px), calc(-50% + ${state.y * STICK_RADIUS}px))` }}
        />
      </div>

      <div className="flex flex-col-reverse items-end gap-8 pointer-events-auto touch-none">
        <button
          className="h-[180px] w-[180px] rounded-full border-2 border-rust bg-rust/10 font-mono text-5xl text-rust active:scale-90 transition-transform touch-none"
          onPointerDown={(e) => { e.currentTarget.setPointerCapture(e.pointerId); setButton('jump', true); }}
          onPointerUp={() => setButton('jump', false)}
          onPointerCancel={() => setButton('jump', false)}
        >
          A
        </button>
        <button
          className="h-[140px] w-[140px] rounded-full border-2 border-ink bg-white/10 font-mono text-4xl text-ink active:scale-90 transition-transform touch-none"
          onPointerDown={(e) => { e.currentTarget.setPointerCapture(e.pointerId); setButton('sprint', true); }}
          onPointerUp={() => setButton('sprint', false)}
          onPointerCancel={() => setButton('sprint', false)}
        >
          B
        </button>
      </div>
    </div>
  );
}
