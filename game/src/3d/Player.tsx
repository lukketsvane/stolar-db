import { useEffect, useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { RigidBody, RapierRigidBody, CapsuleCollider } from '@react-three/rapier';
import * as THREE from 'three';
import { ChairMesh } from './ChairMesh';
import { ChairStack, type StackedChair } from './ChairStack';
import { useKeys } from './useKeys';
import { CHAIR_STACK_PITCH, CHAIR_VISUAL_SCALE } from './GlbChair';
import type { ChairKind, Phase } from '../../shared/protocol';

interface Props {
  name: string;
  kind: ChairKind;
  color: string;
  spawn: [number, number, number];
  score: number;
  phase: Phase;
  serverPos: { x: number; y: number; z: number };
  stackedChairs: StackedChair[];
  onTransform: (x: number, y: number, z: number, yaw: number) => void;
  onBump: (intensity: number) => void;
}

const WALK_SPEED = 8;
const SPRINT_SPEED = 12.5;
const JUMP_VY = 7.4;
const TURN_SPEED = 6;
const CAPSULE_HALF_HEIGHT = 0.4;
const CAPSULE_RADIUS = 0.4;
const BUMP_SPEED_THRESHOLD = 5.0;   // m/s relative speed at impact
const BUMP_COOLDOWN_MS = 700;
const BASE_CHAIR_TOP = CHAIR_VISUAL_SCALE;

export function Player({ name, kind, color, spawn, score, phase, serverPos, stackedChairs, onTransform, onBump }: Props) {
  const body = useRef<RapierRigidBody>(null);
  const yaw = useRef(0);
  const grounded = useRef(false);
  const groupRef = useRef<THREE.Group>(null);
  const keys = useKeys();
  const lastBumpAt = useRef(0);

  useEffect(() => {
    if (body.current) {
      body.current.setTranslation({ x: spawn[0], y: spawn[1], z: spawn[2] }, true);
      body.current.setLinvel({ x: 0, y: 0, z: 0 }, true);
    }
  }, [spawn]);

  const lastPhaseKind = useRef<string>(phase.kind);
  useEffect(() => {
    if (!body.current) return;
    if (phase.kind !== lastPhaseKind.current) {
      lastPhaseKind.current = phase.kind;
      body.current.setTranslation({ x: serverPos.x, y: serverPos.y + 0.5, z: serverPos.z }, true);
      body.current.setLinvel({ x: 0, y: 0, z: 0 }, true);
    }
  }, [phase.kind, serverPos.x, serverPos.y, serverPos.z]);

  useFrame((state, dt) => {
    const rb = body.current;
    if (!rb) return;
    const k = keys.current;
    const cam = state.camera;
    const forward = new THREE.Vector3();
    cam.getWorldDirection(forward);
    forward.y = 0; forward.normalize();
    const right = new THREE.Vector3().crossVectors(forward, new THREE.Vector3(0, 1, 0)).normalize();

    const move = new THREE.Vector3();
    if (k.forward) move.add(forward);
    if (k.back) move.sub(forward);
    if (k.right) move.add(right);
    if (k.left) move.sub(right);
    const speed = k.sprint ? SPRINT_SPEED : WALK_SPEED;
    if (move.lengthSq() > 0) move.normalize().multiplyScalar(speed);

    const lin = rb.linvel();
    rb.setLinvel({ x: move.x, y: lin.y, z: move.z }, true);

    if (move.lengthSq() > 0.1) {
      const targetYaw = Math.atan2(move.x, move.z);
      let dy = targetYaw - yaw.current;
      while (dy > Math.PI) dy -= Math.PI * 2;
      while (dy < -Math.PI) dy += Math.PI * 2;
      yaw.current += dy * Math.min(1, dt * TURN_SPEED);
    }

    const pos = rb.translation();
    if (Math.abs(lin.y) < 0.1 && pos.y < CAPSULE_HALF_HEIGHT + CAPSULE_RADIUS + 0.2) {
      grounded.current = true;
    } else {
      grounded.current = false;
    }
    if (k.jump && grounded.current) {
      rb.setLinvel({ x: lin.x, y: JUMP_VY, z: lin.z }, true);
      grounded.current = false;
    }

    // High orthographic follow camera: keeps the arena legible from above
    // while preserving a little Fall Guys-style 3D depth.
    const stackHeight = BASE_CHAIR_TOP + stackedChairs.length * CHAIR_STACK_PITCH;
    const stackBonus = Math.min(stackedChairs.length, 10);
    const lookAheadZ = phase.kind === 'arena' ? -5.5 : 0;
    const camTarget = new THREE.Vector3(pos.x, 0.6 + stackHeight * 0.25, pos.z + lookAheadZ);
    const desired = new THREE.Vector3(
      pos.x,
      pos.y + 22 + stackBonus * 0.55,
      pos.z + 13 + stackBonus * 0.22
    );
    cam.position.lerp(desired, Math.min(1, dt * 5));
    cam.lookAt(camTarget);
    const ortho = cam as THREE.OrthographicCamera;
    if (ortho.isOrthographicCamera) {
      const compact = state.size.width < 640;
      const targetWorldWidth = compact ? 32 : 56;
      const targetWorldHeight = compact ? 62 : 46;
      const responsiveZoom = Math.min(
        state.size.width / targetWorldWidth,
        state.size.height / targetWorldHeight
      );
      const targetZoom = THREE.MathUtils.clamp((responsiveZoom - stackBonus * 0.45) * 4, 28, 64);
      ortho.zoom = THREE.MathUtils.lerp(ortho.zoom, targetZoom, Math.min(1, dt * 3));
      ortho.updateProjectionMatrix();
    }

    if (groupRef.current) groupRef.current.rotation.y = yaw.current;
    onTransform(pos.x, pos.y, pos.z, yaw.current);
  });

  return (
    <RigidBody
      ref={body}
      colliders={false}
      type="dynamic"
      enabledRotations={[false, false, false]}
      position={spawn}
      linearDamping={2.0}
      angularDamping={4.0}
      friction={0.7}
      onCollisionEnter={(e) => {
        const rb = body.current;
        if (!rb) return;
        const lin = rb.linvel();
        const speed = Math.sqrt(lin.x * lin.x + lin.z * lin.z);
        if (speed < BUMP_SPEED_THRESHOLD) return;
        const now = Date.now();
        if (now - lastBumpAt.current < BUMP_COOLDOWN_MS) return;
        lastBumpAt.current = now;
        onBump(speed);
      }}
    >
      <CapsuleCollider args={[CAPSULE_HALF_HEIGHT, CAPSULE_RADIUS]} position={[0, CAPSULE_HALF_HEIGHT + CAPSULE_RADIUS, 0]} />
      <group ref={groupRef} position={[0, 0, 0]}>
        <ChairMesh kind={kind} color={color} scale={CHAIR_VISUAL_SCALE} />
        <ChairStack chairs={stackedChairs} baseTop={BASE_CHAIR_TOP} />
        {/* Self has no nameplate — only remote players show one. */}
      </group>
    </RigidBody>
  );
}
