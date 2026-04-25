import { useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { ChairMesh } from '../3d/ChairMesh';
import { Stage, OrbitControls } from '@react-three/drei';
import type { ChairKind } from '../../shared/protocol';
import { COLORS } from '../net/useNet';

interface Props {
  onJoin: (name: string, kind: ChairKind, color: string) => void;
  roomId?: string | null;
}

const KINDS: { k: ChairKind; namn: string }[] = [
  { k: 0, namn: 'enkel' },
  { k: 1, namn: 'pinneryggad' },
  { k: 2, namn: 'h-rygg + armar' },
  { k: 3, namn: 'rund' },
  { k: 4, namn: 'polstra' },
  { k: 5, namn: 'høg modernist' },
];

const KAKE = ['Krem', 'Marsipan', 'Sukkerbrød', 'Glasur', 'Botn', 'Bær', 'Fyll', 'Strøssel', 'Lys', 'Kakefat'];
const MATERIE = ['Tre', 'Metall', 'Plast', 'Lær', 'Tekstil', 'Rotting', 'Furu', 'Eik', 'Stål', 'Krom'];

const randomName = () => {
  const k = KAKE[Math.floor(Math.random() * KAKE.length)];
  const m = MATERIE[Math.floor(Math.random() * MATERIE.length)];
  return `${k}-${m.toLowerCase()}`;
};

export function PreGameLobby({ onJoin, roomId }: Props) {
  const [name, setName] = useState(randomName);
  const [kind, setKind] = useState<ChairKind>(0);
  const [color, setColor] = useState(COLORS[Math.floor(Math.random() * COLORS.length)]);

  const changeName = () => {
    setName(randomName());
  };

  return (
    <div className="fixed inset-0 flex items-center justify-center p-4 bg-bg overflow-hidden">
      <div className="w-full max-w-4xl h-full max-h-[640px] md:max-h-[520px] card-hard overflow-hidden flex flex-col md:flex-row border-paper">
        
        {/* Left/Top: 3D Preview */}
        <div className="relative flex-1 bg-white/40 border-b md:border-b-0 md:border-r border-paper/20 overflow-hidden">
          <Canvas camera={{ position: [1.2, 1.2, 2], fov: 35 }}>
            <color attach="background" args={['#FFFFFF']} />
            <Stage intensity={1.05} environment="city" adjustCamera={false}>
              <ChairMesh kind={kind} color={color} scale={1.18} />
            </Stage>
            <OrbitControls enablePan={false} autoRotate autoRotateSpeed={1.2} />
          </Canvas>
        </div>

        {/* Right/Bottom: Controls */}
        <div className="flex-[1.2] p-4 md:p-6 flex flex-col text-center md:text-left min-h-0">
          <div className="mb-6">
            <h1
              onClick={changeName}
              className="font-serif text-5xl text-paper cursor-pointer hover:text-[#5F8EE8] transition-colors select-none"
            >
              {name}
            </h1>
          </div>

          <div
            className="flex-1 min-h-0 space-y-10 px-3 py-3 scrollbar-hide"
            style={{ overflowX: 'visible', overflowY: 'auto' }}
          >
            <section>
              <div className="grid grid-cols-3 gap-3">
                {KINDS.map(({ k, namn }) => (
                  <button
                    key={k}
                    onClick={() => setKind(k)}
                    className={`px-1 py-4 font-mono text-[9px] uppercase tracking-wider border-2 transition-all leading-tight ${
                      kind === k
                        ? 'border-paper text-[#4B7FDC] bg-[#EAF2FF] translate-x-[1px] translate-y-[1px] shadow-none'
                        : 'border-paper text-inkSoft bg-white/60 hover:bg-white btn-hard'
                    }`}
                  >
                    {namn}
                  </button>
                ))}
              </div>
            </section>

            <section>
              <div className="grid grid-cols-8 md:grid-cols-4 gap-5 px-3 py-3">
                {COLORS.map((c) => (
                  <div key={c} className="flex items-center justify-center">
                    <button
                      onClick={() => {
                        setColor(c);
                        onJoin(name, kind, c);
                      }}
                      className={`aspect-square w-[80%] rounded-full border-2 transition-all active:scale-90 ${color === c ? 'border-paper ring-4 ring-paper/10 scale-110 z-10 shadow-none' : 'border-paper btn-hard hover:scale-105'}`}
                      style={{ backgroundColor: c }}
                      aria-label={c}
                    />
                  </div>
                ))}
              </div>
            </section>
          </div>

          <div className="mt-4 pt-4 border-t border-rule/5">
             <div className="font-mono text-[8px] uppercase tracking-widest text-inkSoft/40">stablar &copy; 2026</div>
          </div>
        </div>
      </div>
    </div>
  );
}
