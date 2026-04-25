import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { Physics, RigidBody } from '@react-three/rapier';
import { Suspense, useMemo, useRef } from 'react';
import * as THREE from 'three';
import { Player } from './Player';
import { Remote } from './Remote';
import { StableArena } from '../arenas/Stable';
import type { StackedChair } from './ChairStack';
import type { Phase, PlayerState } from '../../shared/protocol';
import { STABLE_ARENA, stableSpawnPosition } from '../../shared/arena';

interface Props {
  myId: string | null;
  players: PlayerState[];
  phase: Phase;
  myX: number;
  myZ: number;
  stackedChairs: StackedChair[];
  onTransform: (x: number, y: number, z: number, yaw: number) => void;
  onPickup: (pid: string) => void;
  onBump: (otherId: string, intensity: number) => void;
}

function WorldCamera({ x, z, stackCount, phase }: { x: number; z: number; stackCount: number; phase: Phase }) {
  const { camera, size } = useThree();
  const smoothPos = useRef(new THREE.Vector3());
  const initialized = useRef(false);

  useFrame((_, dt) => {
    const stackBonus = Math.min(stackCount, 10);
    const screenOffsetZ = phase.kind === 'arena' ? 2.6 : 0;
    const desired = new THREE.Vector3(x, 35 + stackBonus * 0.45, z + screenOffsetZ);

    if (!initialized.current) {
      smoothPos.current.copy(desired);
      initialized.current = true;
    }

    smoothPos.current.lerp(desired, 1 - Math.exp(-7 * dt));

    camera.position.copy(smoothPos.current);
    camera.rotation.set(-Math.PI / 2, 0, 0);

    const ortho = camera as THREE.OrthographicCamera;
    if (ortho.isOrthographicCamera) {
      const compact = size.width < 640;
      const targetWorldWidth = compact ? 24 : 34;
      const targetWorldHeight = compact ? 38 : 28;
      const responsiveZoom = Math.min(size.width / targetWorldWidth, size.height / targetWorldHeight);
      const targetZoom = THREE.MathUtils.clamp((responsiveZoom - stackBonus * 0.28) * 4, 62, 104);
      ortho.zoom = THREE.MathUtils.lerp(ortho.zoom, targetZoom, 1 - Math.exp(-3 * dt));
      ortho.updateProjectionMatrix();
    }
  }, 2);

  return null;
}

export function World({ myId, players, phase, myX, myZ, stackedChairs, onTransform, onPickup, onBump }: Props) {
  const me = players.find((p) => p.id === myId);
  const others = players.filter((p) => p.id !== myId);
  const hasLocalTransform = Math.abs(myX) > 0.001 || Math.abs(myZ) > 0.001;
  const cameraX = hasLocalTransform ? myX : me?.x ?? 0;
  const cameraZ = hasLocalTransform ? myZ : me?.z ?? STABLE_ARENA.spawnZ;

  const spawn = useMemo<[number, number, number]>(() => {
    if (me) return [me.x, me.y, me.z];
    const p = stableSpawnPosition(0);
    return [p.x, p.y, p.z];
  }, [myId, !!me]);

  return (
    <Canvas
      orthographic
      shadows={{ type: THREE.BasicShadowMap }}
      camera={{ position: [0, 34, 0], zoom: 84, near: 0.1, far: 260 }}
      gl={{
        antialias: true,
        alpha: false,
        powerPreference: 'high-performance',
        preserveDrawingBuffer: location.hostname === '127.0.0.1' || location.hostname === 'localhost',
      }}
      dpr={[1, 1.5]}
    >
      <WorldCamera x={cameraX} z={cameraZ} stackCount={stackedChairs.length} phase={phase} />
      <color attach="background" args={['#FFFFFF']} />
      <fog attach="fog" args={['#FFFFFF', 90, 190]} />

      <ambientLight intensity={0.78} color="#ffffff" />

      <directionalLight
        castShadow
        position={[20, 30, 10]}
        intensity={2.05}
        color="#fff5df"
        shadow-mapSize={[2048, 2048]}
        shadow-camera-left={-30}
        shadow-camera-right={30}
        shadow-camera-top={30}
        shadow-camera-bottom={-30}
        shadow-camera-near={8}
        shadow-camera-far={70}
      />

      <directionalLight position={[-12, 14, -10]} intensity={0.9} color="#9bc9ff" />

      <hemisphereLight args={['#ffffff', '#dce8f7', 0.82]} />

      <Suspense fallback={null}>
        <Physics gravity={[0, -16, 0]}>
          {phase.kind === 'arena' && phase.arenaId === 'stable' && (
            <StableArena
              data={phase.data}
              myId={myId}
              myX={cameraX}
              myZ={cameraZ}
              onPickup={onPickup}
            />
          )}
          {me && (
            <Player
              key={`me-${myId}`}
              name={me.name}
              kind={me.kind}
              color={me.color}
              spawn={spawn}
              score={me.score}
              phase={phase}
              serverPos={{ x: me.x, y: me.y, z: me.z }}
              stackedChairs={stackedChairs}
              onTransform={onTransform}
              onBump={onBump}
            />
          )}
          {others.map((p) => (
            <Remote
              key={p.id}
              id={p.id}
              name={p.name}
              kind={p.kind}
              color={p.color}
              x={p.x} y={p.y} z={p.z} yaw={p.yaw}
              score={p.score}
              stack={p.stack}
            />
          ))}
        </Physics>
      </Suspense>
    </Canvas>
  );
}
