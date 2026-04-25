import { Suspense, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { GlbChair, CHAIR_STACK_PITCH, CHAIR_TARGET_H } from './GlbChair';

export interface StackedChair {
  chairId: string;
  glbPath: string;
}

interface Props {
  /** chairs in stack order (bottom = index 0). The player's BASE chair
   *  (procedural) is drawn separately by the parent and is NOT included. */
  chairs: StackedChair[];
  /** vertical offset of the bottom of the first stacked chair, above the
   *  player origin. */
  baseTop: number;
}

// Renders a stack of N chairs above the player, all normalised to the
// character's ~1 m height. Wobble proportional to stack height.
export function ChairStack({ chairs, baseTop }: Props) {
  const ref = useRef<THREE.Group>(null);

  useFrame((state) => {
    const g = ref.current;
    if (!g) return;
    const t = state.clock.elapsedTime;
    const danger = chairs.length > 4 ? (chairs.length - 4) * 0.05 : 0;
    const wobble = Math.min(0.34, chairs.length * 0.018 + danger);
    g.rotation.x = Math.sin(t * 1.3) * wobble * 0.6 + Math.sin(t * 4.1) * danger * 0.3;
    g.rotation.z = Math.cos(t * 1.7) * wobble + Math.cos(t * 5.3) * danger * 0.4;
  });

  if (!chairs.length) return null;

  return (
    <group ref={ref} position={[0, baseTop, 0]}>
      {chairs.map((c, i) => (
        <group
          key={`${i}-${c.chairId}`}
          position={[0, i * CHAIR_STACK_PITCH, 0]}
          rotation={[0, ((i % 2) - 0.5) * 0.4, 0]}
        >
          <Suspense fallback={null}>
            <GlbChair glbPath={c.glbPath} targetHeight={CHAIR_TARGET_H} />
          </Suspense>
        </group>
      ))}
    </group>
  );
}
