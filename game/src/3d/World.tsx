import { Canvas } from '@react-three/fiber';
import { Physics, RigidBody } from '@react-three/rapier';
import { Suspense, useMemo } from 'react';
import { Player } from './Player';
import { Remote } from './Remote';
import { StableArena } from '../arenas/Stable';
import type { StackedChair } from './ChairStack';
import type { Phase, PlayerState } from '../../shared/protocol';
import { stableSpawnPosition } from '../../shared/arena';

interface Props {
  myId: string | null;
  players: PlayerState[];
  phase: Phase;
  myX: number;
  myZ: number;
  stackedChairs: StackedChair[];
  onTransform: (x: number, y: number, z: number, yaw: number) => void;
  onPickup: (pid: string) => void;
  onBump: (intensity: number) => void;
}

export function World({ myId, players, phase, myX, myZ, stackedChairs, onTransform, onPickup, onBump }: Props) {
  const me = players.find((p) => p.id === myId);
  const others = players.filter((p) => p.id !== myId);

  const spawn = useMemo<[number, number, number]>(() => {
    const idx = Math.max(0, players.findIndex((p) => p.id === myId));
    const p = stableSpawnPosition(idx);
    return [p.x, p.y, p.z];
  }, [myId, players.length]);

  return (
    <Canvas
      orthographic
      camera={{ position: [0, 23, 0], zoom: 64, near: 0.1, far: 220 }}
      gl={{
        antialias: true,
        powerPreference: 'high-performance',
        preserveDrawingBuffer: location.hostname === '127.0.0.1' || location.hostname === 'localhost',
      }}
      dpr={[1, 1.5]}
    >
      <Suspense fallback={null}>
        <color attach="background" args={['#FBF8F1']} />
        <fog attach="fog" args={['#FBF8F1', 80, 180]} />

        <ambientLight intensity={0.78} color="#ffffff" />

        <directionalLight position={[14, 22, 10]} intensity={1.6} color="#fff5df" />

        <directionalLight position={[-12, 14, -10]} intensity={0.9} color="#9bc9ff" />

        <hemisphereLight args={['#ffffff', '#dce8f7', 0.82]} />

        <Physics gravity={[0, -16, 0]}>
          {phase.kind === 'arena' && phase.arenaId === 'stable' && (
            <StableArena
              data={phase.data}
              myId={myId}
              myX={myX}
              myZ={myZ}
              onPickup={onPickup}
            />
          )}
          {phase.kind !== 'arena' && (
            <RigidBody type="fixed" colliders="cuboid">
              <mesh position={[0, -0.05, 0]} receiveShadow>
                <boxGeometry args={[80, 0.1, 80]} />
                <meshStandardMaterial color="#F7F3EA" roughness={0.9} />
              </mesh>
            </RigidBody>
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
              name={p.name}
              kind={p.kind}
              color={p.color}
              x={p.x} y={p.y} z={p.z} yaw={p.yaw}
              score={p.score}
            />
          ))}
        </Physics>
      </Suspense>
    </Canvas>
  );
}
