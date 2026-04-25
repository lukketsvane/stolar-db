import { Billboard, Text } from '@react-three/drei';

interface Props {
  name: string;
  score: number;
  /** y-offset above the rigid body origin (default 1.45). */
  y?: number;
}

export function Nameplate({ name, score, y = 1.45 }: Props) {
  return (
    <Billboard position={[0, y, 0]}>
      <Text
        fontSize={0.22}
        color="#101828"
        outlineColor="#FFFFFF"
        outlineWidth={0.024}
        anchorX="center"
        anchorY="middle"
      >
        {name}
      </Text>
      <Text
        position={[0, -0.28, 0]}
        fontSize={0.18}
        color="#F0643B"
        outlineColor="#FFFFFF"
        outlineWidth={0.022}
        anchorX="center"
        anchorY="middle"
      >
        × {score}
      </Text>
    </Billboard>
  );
}
