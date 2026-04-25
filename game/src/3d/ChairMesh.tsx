import { forwardRef } from 'react';
import * as THREE from 'three';
import type { ChairKind } from '../../shared/protocol';

interface Props {
  kind: ChairKind;
  color: string;
  scale?: number;
}

// 6 procedural low-poly chair archetypes. All share a 1m total height,
// ~0.6m wide footprint. Origin = bottom-center.
export const ChairMesh = forwardRef<THREE.Group, Props>(function ChairMesh(
  { kind, color, scale = 1 }, ref
) {
  const woodMat = <meshStandardMaterial color={color} roughness={0.7} metalness={0.05} />;
  const seatMat = <meshStandardMaterial color={color} roughness={0.55} metalness={0.05} />;

  const seatH = 0.5;        // seat top z
  const seatT = 0.05;       // seat thickness
  const totalH = 1.0;       // seat back top
  const W = 0.55, D = 0.55;
  const legR = 0.04;

  const Leg = ({ x, z }: { x: number; z: number }) => (
    <mesh position={[x, seatH / 2, z]} castShadow>
      <cylinderGeometry args={[legR, legR * 1.1, seatH, 10]} />
      {woodMat}
    </mesh>
  );

  const Seat = (
    <mesh position={[0, seatH + seatT / 2, 0]} castShadow>
      <boxGeometry args={[W, seatT, D]} />
      {seatMat}
    </mesh>
  );

  const SimpleBack = (
    <mesh position={[0, seatH + (totalH - seatH) / 2, -D / 2 + 0.04]} castShadow>
      <boxGeometry args={[W * 0.95, totalH - seatH - 0.05, 0.05]} />
      {woodMat}
    </mesh>
  );

  const SpindleBack = (
    <group>
      {[-0.18, -0.06, 0.06, 0.18].map((x, i) => (
        <mesh key={i} position={[x, seatH + (totalH - seatH) / 2, -D / 2 + 0.04]} castShadow>
          <cylinderGeometry args={[0.02, 0.02, totalH - seatH - 0.05, 8]} />
          {woodMat}
        </mesh>
      ))}
      <mesh position={[0, totalH - 0.04, -D / 2 + 0.04]} castShadow>
        <boxGeometry args={[W, 0.07, 0.07]} />
        {woodMat}
      </mesh>
    </group>
  );

  const HBack = (
    <group>
      <mesh position={[-W / 2 + 0.04, seatH + (totalH - seatH) / 2, -D / 2 + 0.04]} castShadow>
        <boxGeometry args={[0.06, totalH - seatH - 0.05, 0.06]} />
        {woodMat}
      </mesh>
      <mesh position={[W / 2 - 0.04, seatH + (totalH - seatH) / 2, -D / 2 + 0.04]} castShadow>
        <boxGeometry args={[0.06, totalH - seatH - 0.05, 0.06]} />
        {woodMat}
      </mesh>
      <mesh position={[0, seatH + (totalH - seatH) * 0.7, -D / 2 + 0.04]} castShadow>
        <boxGeometry args={[W * 0.85, 0.05, 0.05]} />
        {woodMat}
      </mesh>
    </group>
  );

  const RoundBack = (
    <group>
      <mesh position={[0, seatH + (totalH - seatH) / 2 + 0.02, -D / 2 + 0.04]} castShadow>
        <torusGeometry args={[(totalH - seatH) / 2 - 0.04, 0.025, 8, 24, Math.PI]} />
        {woodMat}
      </mesh>
      {/* vertical supports for the curve */}
      <mesh position={[-W / 2 + 0.08, seatH + (totalH - seatH) / 4, -D / 2 + 0.04]} castShadow>
        <cylinderGeometry args={[0.02, 0.02, (totalH - seatH) / 2, 8]} />
        {woodMat}
      </mesh>
      <mesh position={[W / 2 - 0.08, seatH + (totalH - seatH) / 4, -D / 2 + 0.04]} castShadow>
        <cylinderGeometry args={[0.02, 0.02, (totalH - seatH) / 2, 8]} />
        {woodMat}
      </mesh>
    </group>
  );

  const ArmRest = (
    <>
      <mesh position={[-W / 2, seatH + 0.18, 0]} castShadow>
        <boxGeometry args={[0.05, 0.04, D - 0.1]} />
        {woodMat}
      </mesh>
      <mesh position={[W / 2, seatH + 0.18, 0]} castShadow>
        <boxGeometry args={[0.05, 0.04, D - 0.1]} />
        {woodMat}
      </mesh>
    </>
  );

  let backNode: React.ReactNode = SimpleBack;
  let arms: React.ReactNode = null;
  let extra: React.ReactNode = null;

  switch (kind) {
    case 0: backNode = SimpleBack; break;
    case 1: backNode = SpindleBack; break;
    case 2: backNode = HBack; arms = ArmRest; break;
    case 3: backNode = RoundBack; break;
    case 4:
      // upholstered: thicker seat, padded back
      backNode = (
        <mesh position={[0, seatH + (totalH - seatH) / 2, -D / 2 + 0.06]} castShadow>
          <boxGeometry args={[W * 0.9, totalH - seatH - 0.08, 0.1]} />
          <meshStandardMaterial color={color} roughness={0.9} />
        </mesh>
      );
      extra = (
        <mesh position={[0, seatH + 0.04, 0]} castShadow>
          <boxGeometry args={[W * 0.95, 0.07, D * 0.95]} />
          <meshStandardMaterial color={color} roughness={0.9} />
        </mesh>
      );
      break;
    case 5:
      // tall thin modern: high back, no arms
      backNode = (
        <mesh position={[0, seatH + (totalH - seatH + 0.2) / 2, -D / 2 + 0.04]} castShadow>
          <boxGeometry args={[W * 0.7, totalH - seatH + 0.2, 0.04]} />
          {woodMat}
        </mesh>
      );
      break;
  }

  return (
    <group ref={ref} scale={scale}>
      <Leg x={-W / 2 + legR} z={-D / 2 + legR} />
      <Leg x={W / 2 - legR} z={-D / 2 + legR} />
      <Leg x={-W / 2 + legR} z={D / 2 - legR} />
      <Leg x={W / 2 - legR} z={D / 2 - legR} />
      {Seat}
      {backNode}
      {arms}
      {extra}
    </group>
  );
});
