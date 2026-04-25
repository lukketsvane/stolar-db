import type { Chair } from './types';

let cache: Chair[] | null = null;

export async function loadChairs(): Promise<Chair[]> {
  if (cache) return cache;
  const res = await fetch('/chairs.json');
  if (!res.ok) throw new Error(`failed to load chairs.json: ${res.status}`);
  const data = (await res.json()) as Chair[];
  cache = data;
  return data;
}

export function chairImg(id: string): string {
  return `/bguw/${id}_bguw.png`;
}

export function pickN<T>(arr: T[], n: number, rng: () => number = Math.random): T[] {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rng() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a.slice(0, n);
}

export function distEmb(a: [number, number, number], b: [number, number, number]): number {
  const dx = a[0] - b[0], dy = a[1] - b[1], dz = a[2] - b[2];
  return Math.sqrt(dx * dx + dy * dy + dz * dz);
}

export function fmtCm(v: number | null | undefined): string {
  if (v == null || !isFinite(v)) return '?';
  return `${Math.round(v)} cm`;
}

export function fmtYear(y: number): string {
  return String(y);
}

export function decadeOf(y: number): number {
  return Math.floor(y / 10) * 10;
}
