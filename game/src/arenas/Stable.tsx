import { CuboidCollider, RigidBody } from '@react-three/rapier';
import { Pickup } from '../3d/Pickup';
import type { StableData, PickupItem } from '../../shared/protocol';
import { STABLE_ARENA, STABLE_OBSTACLES, type StableObstacle } from '../../shared/arena';

interface Props {
  data: StableData;
  myId: string | null;
  myX: number;
  myZ: number;
  onPickup: (pid: string) => void;
}

const HALF_X = STABLE_ARENA.halfX;
const HALF_Z = STABLE_ARENA.halfZ;
const WALL_H = STABLE_ARENA.wallHeight;

export function StableArena({ data, myId, myX, myZ, onPickup }: Props) {
  return (
    <group>
      {/* arena floor */}
      <RigidBody type="fixed" colliders="cuboid">
        <mesh position={[0, -0.05, 0]} receiveShadow>
          <boxGeometry args={[HALF_X * 2, 0.1, HALF_Z * 2]} />
          <meshStandardMaterial color="#F9FAFD" roughness={0.88} />
        </mesh>
      </RigidBody>

      <FloorPanels />

      {/* perimeter walls */}
      <RigidBody type="fixed" colliders="cuboid">
        <mesh position={[HALF_X + 0.5, WALL_H / 2, 0]} castShadow>
          <boxGeometry args={[1, WALL_H, HALF_Z * 2 + 2]} />
          <meshStandardMaterial color="#DCEBFF" roughness={0.76} />
        </mesh>
      </RigidBody>
      <RigidBody type="fixed" colliders="cuboid">
        <mesh position={[-HALF_X - 0.5, WALL_H / 2, 0]} castShadow>
          <boxGeometry args={[1, WALL_H, HALF_Z * 2 + 2]} />
          <meshStandardMaterial color="#DCEBFF" roughness={0.76} />
        </mesh>
      </RigidBody>
      <RigidBody type="fixed" colliders="cuboid">
        <mesh position={[0, WALL_H / 2, HALF_Z + 0.5]} castShadow>
          <boxGeometry args={[HALF_X * 2 + 2, WALL_H, 1]} />
          <meshStandardMaterial color="#FFE4A8" roughness={0.76} />
        </mesh>
      </RigidBody>
      <RigidBody type="fixed" colliders="cuboid">
        <mesh position={[0, WALL_H / 2, -HALF_Z - 0.5]} castShadow>
          <boxGeometry args={[HALF_X * 2 + 2, WALL_H, 1]} />
          <meshStandardMaterial color="#FFE4A8" roughness={0.76} />
        </mesh>
      </RigidBody>

      {/* readable board markings for the top-down camera */}
      {Array.from({ length: 7 }).map((_, i) => {
        const z = -HALF_Z + (i + 1) * (HALF_Z * 2 / 8);
        return (
          <mesh key={`g-${i}`} position={[0, 0.005, z]} rotation={[-Math.PI / 2, 0, 0]}>
            <planeGeometry args={[HALF_X * 2, 0.05]} />
            <meshBasicMaterial color="#B8C6D9" transparent opacity={0.55} />
          </mesh>
        );
      })}
      {[-12, 0, 12].map((x) => (
        <mesh key={`lane-${x}`} position={[x, 0.006, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[0.06, HALF_Z * 2]} />
          <meshBasicMaterial color="#B8C6D9" transparent opacity={0.48} />
        </mesh>
      ))}

      {STABLE_OBSTACLES.map((o) => <CourseBlock key={o.id} obstacle={o} />)}

      {/* pickups */}
      {data.pickups.map((p) => (
        <PickupGate
          key={p.pid}
          item={p}
          myX={myX}
          myZ={myZ}
          onTake={() => onPickup(p.pid)}
        />
      ))}
    </group>
  );
}

function FloorPanels() {
  return (
    <>
      <mesh position={[0, 0.003, STABLE_ARENA.spawnZ]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[HALF_X * 2 - 3, 5.2]} />
        <meshBasicMaterial color="#BFEAD7" transparent opacity={0.72} />
      </mesh>
      <mesh position={[0, 0.004, -HALF_Z + 4]} rotation={[-Math.PI / 2, 0, 0]}>
        <planeGeometry args={[HALF_X * 2 - 4, 4.5]} />
        <meshBasicMaterial color="#DCD6FF" transparent opacity={0.62} />
      </mesh>
      {[-18, 18].map((x) => (
        <mesh key={`side-stripe-${x}`} position={[x, 0.007, 0]} rotation={[-Math.PI / 2, 0, 0]}>
          <planeGeometry args={[1.2, HALF_Z * 2 - 4]} />
          <meshBasicMaterial color="#FFD56B" transparent opacity={0.42} />
        </mesh>
      ))}
    </>
  );
}

function CourseBlock({ obstacle }: { obstacle: StableObstacle }) {
  return (
    <RigidBody
      type="fixed"
      colliders={false}
      position={[obstacle.x, 0.45, obstacle.z]}
      rotation={[0, obstacle.yaw, 0]}
    >
      <CuboidCollider args={[obstacle.w / 2, 0.45, obstacle.d / 2]} />
      <mesh castShadow receiveShadow>
        <boxGeometry args={[obstacle.w, 0.9, obstacle.d]} />
        <meshStandardMaterial color={obstacle.color} roughness={0.72} metalness={0.02} />
      </mesh>
      <mesh position={[0, 0.47, 0]}>
        <boxGeometry args={[obstacle.w * 0.92, 0.04, obstacle.d * 0.75]} />
        <meshBasicMaterial color="#FFFFFF" transparent opacity={0.34} />
      </mesh>
    </RigidBody>
  );
}

interface GateProps {
  item: PickupItem;
  myX: number;
  myZ: number;
  onTake: () => void;
}

function PickupGate({ item, myX, myZ, onTake }: GateProps) {
  if (item.takenBy) return null;
  const dx = myX - item.x;
  const dz = myZ - item.z;
  const near = dx * dx + dz * dz < 1.6 * 1.6;

  return <Pickup item={item} near={near} onTake={onTake} />;
}
