import { useEffect, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { ChairMesh } from './ChairMesh';
import { ChairStack, type StackedChair } from './ChairStack';
import { Nameplate } from './Nameplate';
import { CHAIR_STACK_PITCH, CHAIR_VISUAL_SCALE } from './GlbChair';
import type { ChairKind } from '../../shared/protocol';

const FALLBACK: StackedChair = { chairId: 'opsvik', glbPath: '/pbr/opsvik.glb' };
const BASE_CHAIR_TOP = CHAIR_VISUAL_SCALE;

interface Props {
  name: string;
  kind: ChairKind;
  color: string;
  x: number; y: number; z: number; yaw: number;
  score: number;
}

export function Remote({ name, kind, color, x, y, z, yaw, score }: Props) {
  const ref = useRef<THREE.Group>(null);
  const target = useRef(new THREE.Vector3(x, y, z));
  const targetYaw = useRef(yaw);

  useEffect(() => {
    target.current.set(x, y, z);
    targetYaw.current = yaw;
  }, [x, y, z, yaw]);

  useFrame((_, dt) => {
    const g = ref.current;
    if (!g) return;
    g.position.lerp(target.current, Math.min(1, dt * 14));
    let dy = targetYaw.current - g.rotation.y;
    while (dy > Math.PI) dy -= Math.PI * 2;
    while (dy < -Math.PI) dy += Math.PI * 2;
    g.rotation.y += dy * Math.min(1, dt * 12);
  });

  // For remotes we don't know which chairs they picked, so we show `score`
  // instances of a fallback PBR chair as their stack.
  const stack = Array.from({ length: score }, () => FALLBACK);

  return (
    <group ref={ref} position={[x, y, z]} rotation={[0, yaw, 0]}>
      <ChairMesh kind={kind} color={color} scale={CHAIR_VISUAL_SCALE} />
      <ChairStack chairs={stack} baseTop={BASE_CHAIR_TOP} />
      <Nameplate
        name={name}
        score={score}
        y={BASE_CHAIR_TOP + score * CHAIR_STACK_PITCH + 0.4}
      />
    </group>
  );
}
