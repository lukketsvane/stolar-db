import { useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { ChairMesh } from '../3d/ChairMesh';
import { Stage, OrbitControls } from '@react-three/drei';
import type { ChairKind } from '../../shared/protocol';
import { COLORS } from '../net/useNet';

interface Props {
  onJoin: (name: string, kind: ChairKind, color: string) => void;
}

const KINDS: { k: ChairKind; namn: string }[] = [
  { k: 0, namn: 'enkel' },
  { k: 1, namn: 'pinneryggad' },
  { k: 2, namn: 'h-rygg + armar' },
  { k: 3, namn: 'rund' },
  { k: 4, namn: 'polstra' },
  { k: 5, namn: 'høg modernist' },
];

export function PreGameLobby({ onJoin }: Props) {
  const [name, setName] = useState(() => `gjest ${Math.floor(Math.random() * 99) + 1}`);
  const [kind, setKind] = useState<ChairKind>(0);
  const [color, setColor] = useState(COLORS[Math.floor(Math.random() * COLORS.length)]);

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-3xl card p-8 grid md:grid-cols-[1fr_1fr] gap-8 items-center">
        <div className="aspect-square rounded-sm bg-white/70 border border-rule/70 overflow-hidden">
          <Canvas shadows camera={{ position: [1.2, 1.2, 2], fov: 35 }}>
            <color attach="background" args={['#FFFFFF']} />
            <Stage intensity={1.05} environment="city" adjustCamera={false}>
              <ChairMesh kind={kind} color={color} scale={1.18} />
            </Stage>
            <OrbitControls enablePan={false} autoRotate autoRotateSpeed={1.2} />
          </Canvas>
        </div>

        <div>
          <div className="font-mono text-[11px] uppercase tracking-[0.2em] text-[#5F8EE8] mb-2">stolspel</div>
          <h1 className="font-serif text-5xl text-paper mb-1">Vel din stol</h1>
          <p className="font-serif italic text-inkSoft mb-6">Du er stolen. Stolen samlar fleire stolar.</p>

          <label className="block font-mono text-[10px] uppercase tracking-wider text-[#5F8EE8] mb-1">namn</label>
          <input
            value={name}
            onChange={(e) => setName(e.target.value.slice(0, 16))}
            className="w-full bg-white/85 border border-rule px-3 py-2 font-mono text-paper mb-4 focus:outline-none focus:border-[#5F8EE8] focus:ring-2 focus:ring-[#5F8EE8]/20"
            placeholder="namn"
          />

          <label className="block font-mono text-[10px] uppercase tracking-wider text-[#5F8EE8] mb-2">type</label>
          <div className="grid grid-cols-3 gap-1.5 mb-4">
            {KINDS.map(({ k, namn }) => (
              <button
                key={k}
                onClick={() => setKind(k)}
                className={`px-2 py-2 font-mono text-[10px] uppercase tracking-wider border transition-colors ${
                  kind === k
                    ? 'border-[#5F8EE8] text-[#4B7FDC] bg-[#EAF2FF]'
                    : 'border-rule text-inkSoft bg-white/60 hover:border-[#8DB4FA] hover:text-paper'
                }`}
              >
                {namn}
              </button>
            ))}
          </div>

          <label className="block font-mono text-[10px] uppercase tracking-wider text-[#5F8EE8] mb-2">farge</label>
          <div className="flex gap-2 mb-6">
            {COLORS.map((c) => (
              <button
                key={c}
                onClick={() => setColor(c)}
                className={`w-8 h-8 rounded-full border-2 shadow-sm ${color === c ? 'border-[#5F8EE8] ring-2 ring-[#5F8EE8]/25' : 'border-white'}`}
                style={{ backgroundColor: c }}
                aria-label={c}
              />
            ))}
          </div>

          <button onClick={() => onJoin(name || 'gjest', kind, color)} className="btn btn-primary w-full">
            Bli med
          </button>
        </div>
      </div>
    </div>
  );
}
