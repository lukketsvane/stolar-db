import { Suspense, useEffect, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { GlbChair, CHAIR_TARGET_H } from './GlbChair';
import type { PickupItem } from '../../shared/protocol';

interface Props {
  item: PickupItem;
  near: boolean;
  onTake: () => void;
}

// Pickup: non-physical floor chair that spins gently and bobs. Player
// proximity triggers an auto-pickup.
export function Pickup({ item, near, onTake }: Props) {
  const ref = useRef<THREE.Group>(null);
  const taken = useRef(false);
  const lastNear = useRef(false);

  useEffect(() => {
    if (near && !lastNear.current && !taken.current) {
      lastNear.current = true;
      taken.current = true;
      onTake();
    }
    if (!near) lastNear.current = false;
  }, [near, onTake]);

  useFrame((state) => {
    const g = ref.current;
    if (!g) return;
    const t = state.clock.elapsedTime;
    g.rotation.y = t * 0.55 + item.x * 0.1;
    g.position.y = Math.sin(t * 1.3 + item.x * 0.3) * 0.08;
  });

  return (
    <group position={[item.x, 0, item.z]}>
      <group ref={ref} scale={near ? 1.08 : 1.0}>
        <Suspense fallback={null}>
          <GlbChair glbPath={item.glbPath} targetHeight={CHAIR_TARGET_H} />
        </Suspense>
      </group>
    </group>
  );
}
