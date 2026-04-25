export interface Chair {
  id: string;
  namn: string;
  year: number;
  h: number;
  w: number;
  d: number;
  sh: number | null;
  mat: 'tre' | 'metall' | 'plast' | 'lær' | 'tekstil' | 'anna' | 'ukjent';
  stil: string;
  nat: string | null;
  arm: boolean | null;
  pad: boolean | null;
  rygg: string | null;
  bein: number | null;
  emb: [number, number, number] | null;
}

export type RoundId =
  | 'dekade'
  | 'tidslinje'
  | 'odd'
  | 'silhuett'
  | 'dim'
  | 'tvilling'
  | 'proporsjon'
  | 'stolutvalet';

export interface RoundResult {
  id: RoundId;
  score: number;     // 0..100 normalised
  raw: number;       // raw points (game-specific scale)
  detail?: string;   // short summary line
}

export interface GameState {
  step:
    | { kind: 'lobby' }
    | { kind: 'round'; idx: number; rounds: RoundId[] }
    | { kind: 'results'; rounds: RoundId[]; results: RoundResult[] };
  results: RoundResult[];
}
