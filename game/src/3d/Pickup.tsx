import { Suspense, useEffect, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { CuboidCollider, RigidBody, type RapierRigidBody } from '@react-three/rapier';
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
  const body = useRef<RapierRigidBody>(null);
  const taken = useRef(false);
  const lastNear = useRef(false);
  const isDropped = item.pid.startsWith('drop-') || !!item.droppedAt;

  useEffect(() => {
    if (near && !lastNear.current && !taken.current) {
      lastNear.current = true;
      taken.current = true;
      onTake();
    }
    if (!near) lastNear.current = false;
  }, [near, onTake]);

  useEffect(() => {
    if (!isDropped) return;
    const rb = body.current;
    if (!rb) return;
    const yaw = item.dropYaw ?? item.x * 0.17;
    rb.applyImpulse({ x: Math.sin(yaw) * 2.2, y: 3.6, z: Math.cos(yaw) * 2.2 }, true);
    rb.applyTorqueImpulse({ x: 7.5 + item.x * 0.05, y: 2.0, z: -6.5 + item.z * 0.05 }, true);
  }, [isDropped, item.dropYaw, item.pid, item.x, item.z]);

  useFrame((state) => {
    const g = ref.current;
    if (!g) return;
    if (isDropped) return;
    const t = state.clock.elapsedTime;
    g.rotation.y = t * 0.14 + item.x * 0.1;
    g.position.y = Math.sin(t * 1.0 + item.x * 0.3) * 0.05;
  });

  const chair = (
    <group ref={ref} scale={near ? 1.08 : 1.0} rotation={[0, item.dropYaw ?? 0, 0]}>
      <Suspense fallback={null}>
        {item.glbPath && <GlbChair glbPath={item.glbPath} targetHeight={CHAIR_TARGET_H} />}
      </Suspense>
    </group>
  );

  if (isDropped) {
    return (
      <RigidBody
        ref={body}
        type="dynamic"
        colliders={false}
        position={[item.x || 0, 1.35, item.z || 0]}
        rotation={[0.25, item.dropYaw ?? 0, -0.2]}
        linearDamping={1.35}
        angularDamping={0.85}
        restitution={0.18}
        friction={0.82}
      >
        <CuboidCollider args={[0.65, 0.65, 0.65]} />
        {chair}
      </RigidBody>
    );
  }

  return <group position={[item.x || 0, 0, item.z || 0]}>{chair}</group>;
}
