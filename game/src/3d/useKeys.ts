import { useEffect, useRef } from 'react';

export interface KeyState {
  forward: boolean;
  back: boolean;
  left: boolean;
  right: boolean;
  jump: boolean;
  sprint: boolean;
  submit: boolean;
}

interface TouchInput {
  x: number;
  y: number;
  jump: boolean;
  sprint: boolean;
}

const EMPTY_KEYS: KeyState = {
  forward: false, back: false, left: false, right: false, jump: false, sprint: false, submit: false,
};

export function useKeys() {
  const ref = useRef<KeyState>({ ...EMPTY_KEYS });

  useEffect(() => {
    const keyboard: KeyState = { ...EMPTY_KEYS };
    const touch: TouchInput = { x: 0, y: 0, jump: false, sprint: false };

    const sync = () => {
      ref.current.forward = keyboard.forward || touch.y < -0.25;
      ref.current.back = keyboard.back || touch.y > 0.25;
      ref.current.left = keyboard.left || touch.x < -0.25;
      ref.current.right = keyboard.right || touch.x > 0.25;
      ref.current.jump = keyboard.jump || touch.jump;
      ref.current.sprint = keyboard.sprint || touch.sprint;
      ref.current.submit = keyboard.submit;
    };

    const set = (k: keyof KeyState, v: boolean) => { keyboard[k] = v; sync(); };
    const map: Record<string, keyof KeyState> = {
      KeyW: 'forward', ArrowUp: 'forward',
      KeyS: 'back', ArrowDown: 'back',
      KeyA: 'left', ArrowLeft: 'left',
      KeyD: 'right', ArrowRight: 'right',
      Space: 'jump',
      ShiftLeft: 'sprint',
      ShiftRight: 'sprint',
      Enter: 'submit',
    };
    const down = (e: KeyboardEvent) => {
      const k = map[e.code];
      if (k) { set(k, true); if (k === 'jump' || k === 'submit') e.preventDefault(); }
    };
    const up = (e: KeyboardEvent) => {
      const k = map[e.code];
      if (k) set(k, false);
    };
    const mobile = (e: Event) => {
      const d = (e as CustomEvent<TouchInput>).detail;
      touch.x = d?.x ?? 0;
      touch.y = d?.y ?? 0;
      touch.jump = !!d?.jump;
      touch.sprint = !!d?.sprint;
      sync();
    };
    window.addEventListener('keydown', down);
    window.addEventListener('keyup', up);
    window.addEventListener('stolspel:touch-input', mobile as EventListener);
    return () => {
      window.removeEventListener('keydown', down);
      window.removeEventListener('keyup', up);
      window.removeEventListener('stolspel:touch-input', mobile as EventListener);
    };
  }, []);

  return ref;
}
