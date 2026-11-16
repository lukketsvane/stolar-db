import { useEffect, useRef, useState, useCallback } from 'react';
import type { ClientMsg, ServerMsg, PlayerState, Phase, ChairKind } from '../../shared/protocol';

const COLORS = ['#F0643B', '#24A6B8', '#F5BC42', '#9C58C7', '#49B86A', '#EF3F7A', '#FFD15C', '#5F8EE8'];

interface NetState {
  connected: boolean;
  myId: string | null;
  players: PlayerState[];
  phase: Phase;
  ts: number;
}

export interface NetApi extends NetState {
  send: (msg: ClientMsg) => void;
  hello: (name: string, kind: ChairKind, color: string) => void;
  ready: (r: boolean) => void;
  sendInput: (x: number, y: number, z: number, yaw: number) => void;
  pickup: (pid: string) => void;
  bump: (otherId: string, intensity: number) => void;
}

const URL = (() => {
  const configured = (import.meta as unknown as { env?: { VITE_WS_URL?: string } }).env?.VITE_WS_URL?.trim();
  if (configured) return configured;

  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const local = location.hostname === 'localhost' || location.hostname === '127.0.0.1';
  return local ? `${proto}//${location.hostname}:5176` : `${proto}//${location.host}`;
})();

export function useNet(): NetApi {
  const wsRef = useRef<WebSocket | null>(null);
  const [state, setState] = useState<NetState>({
    connected: false, myId: null, players: [], phase: { kind: 'lobby' }, ts: 0,
  });

  useEffect(() => {
    let cancelled = false;
    let ws: WebSocket | null = null;
    let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

    function connect() {
      if (cancelled) return;
      ws = new WebSocket(URL);
      wsRef.current = ws;
      ws.onopen = () => setState((s) => ({ ...s, connected: true }));
      ws.onclose = () => {
        setState((s) => ({ ...s, connected: false }));
        if (!cancelled) reconnectTimer = setTimeout(connect, 1500);
      };
      ws.onerror = () => {};
      ws.onmessage = (ev) => {
        let msg: ServerMsg;
        try { msg = JSON.parse(ev.data); } catch { return; }
        if (msg.t === 'welcome') {
          setState((s) => ({ ...s, myId: msg.id, players: msg.players, phase: msg.phase }));
        } else if (msg.t === 'state') {
          setState((s) => ({ ...s, players: msg.players, phase: msg.phase, ts: msg.ts }));
        } else if (msg.t === 'phase') {
          setState((s) => ({ ...s, phase: msg.phase }));
        } else if (msg.t === 'pickup-result') {
          window.dispatchEvent(new CustomEvent('stolspel:pickup-result', {
            detail: { matched: msg.matched, reason: msg.reason, chairId: msg.chairId, glbPath: msg.glbPath, ts: Date.now() },
          }));
        }
      };
    }

    connect();

    return () => {
      cancelled = true;
      if (reconnectTimer) clearTimeout(reconnectTimer);
      ws?.close();
      wsRef.current = null;
    };
  }, []);

  const send = useCallback((msg: ClientMsg) => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    ws.send(JSON.stringify(msg));
  }, []);

  const hello = useCallback((name: string, kind: ChairKind, color: string) => {
    send({ t: 'hello', name, kind, color });
  }, [send]);

  const ready = useCallback((r: boolean) => {
    send({ t: 'ready', ready: r });
  }, [send]);

  const sendInput = useCallback((x: number, y: number, z: number, yaw: number) => {
    send({ t: 'input', x, y, z, yaw, ts: Date.now() });
  }, [send]);

  const pickup = useCallback((pid: string) => {
    send({ t: 'pickup', pid });
  }, [send]);

  const bump = useCallback((otherId: string, intensity: number) => {
    send({ t: 'bump', otherId, intensity });
  }, [send]);

  return { ...state, send, hello, ready, sendInput, pickup, bump };
}

export { COLORS };
