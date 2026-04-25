import { useEffect, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { RigidBody, RapierRigidBody, CapsuleCollider } from '@react-three/rapier';
import * as THREE from 'three';
import { ChairMesh } from './ChairMesh';
import { ChairStack } from './ChairStack';
import { Nameplate } from './Nameplate';
import { CHAIR_STACK_PITCH, CHAIR_VISUAL_SCALE } from './GlbChair';
import type { ChairKind } from '../../shared/protocol';

const BASE_CHAIR_TOP = CHAIR_VISUAL_SCALE;
const FALLBACK_CHAIR = { chairId: 'wooden_v1', glbPath: '/pbr_textured/wooden_v1.glb' };
const CAPSULE_HALF_HEIGHT = 0.4;
const CAPSULE_RADIUS = 0.4;

interface Props {
  id: string;
  name: string;
  kind: ChairKind;
  color: string;
  x: number; y: number; z: number; yaw: number;
  score: number;
  stack: { chairId: string; glbPath: string }[];
}

export function Remote({ id, name, kind, color, x, y, z, yaw, score, stack = [] }: Props) {
  const body = useRef<RapierRigidBody>(null);
  const visual = useRef<THREE.Group>(null);
  const target = useRef(new THREE.Vector3(x, y, z));

  useEffect(() => {
    if (!isNaN(x) && !isNaN(y) && !isNaN(z)) {
      target.current.set(x, y, z);
    }
  }, [x, y, z]);

  useFrame((_, dt) => {
    const rb = body.current;
    const v = visual.current;
    if (!rb || !v) return;
    if (isNaN(x) || isNaN(y) || isNaN(z)) return;

    const cur = rb.translation();
    const lerp = Math.min(1, dt * 14);
    const nx = cur.x + (target.current.x - cur.x) * lerp;
    const ny = cur.y + (target.current.y - cur.y) * lerp;
    const nz = cur.z + (target.current.z - cur.z) * lerp;
    rb.setNextKinematicTranslation({ x: nx, y: ny, z: nz });

    if (isNaN(yaw)) return;
    let dy = yaw - v.rotation.y;
    while (dy > Math.PI) dy -= Math.PI * 2;
    while (dy < -Math.PI) dy += Math.PI * 2;
    v.rotation.y += dy * Math.min(1, dt * 12);
  });

  const displayScore = isNaN(score) ? 0 : Math.max(0, score);
  const displayStack = (stack && stack.length > 0) ? stack : Array.from({ length: displayScore }, () => FALLBACK_CHAIR);

  return (
    <RigidBody
      ref={body}
      type="kinematicPosition"
      colliders={false}
      position={[x || 0, y || 0, z || 0]}
      userData={{ remotePlayerId: id }}
    >
      <CapsuleCollider args={[CAPSULE_HALF_HEIGHT, CAPSULE_RADIUS]} position={[0, CAPSULE_HALF_HEIGHT + CAPSULE_RADIUS, 0]} />
      <group ref={visual} rotation={[0, yaw || 0, 0]}>
        <ChairMesh kind={kind} color={color} scale={CHAIR_VISUAL_SCALE} />
        <ChairStack chairs={displayStack} baseTop={BASE_CHAIR_TOP} />
        <Nameplate
          name={name}
          score={displayScore}
          y={BASE_CHAIR_TOP + displayScore * CHAIR_STACK_PITCH + 0.4}
        />
      </group>
    </RigidBody>
  );
}
