import { useGLTF } from '@react-three/drei';
import { useMemo } from 'react';
import * as THREE from 'three';

interface Props {
  glbPath?: string;
  chairId?: string;
  position?: [number, number, number];
  rotationY?: number;
  groundAlign?: boolean;
  /** Force the chair's bounding-box height to this many metres. Overrides
   *  any `scale` prop. Default = unset (use native size). */
  targetHeight?: number;
  scale?: number;
}

// Loads a STOLAR GLB and renders it. By default chairs render at their NATIVE
// size; pass `targetHeight` to normalise to a specific height (used to make
// PBR chairs match the player character's ~1 m height).
export function GlbChair({
  glbPath, chairId, position = [0, 0, 0], rotationY = 0,
  groundAlign = true, targetHeight, scale = 1,
}: Props) {
  const url = glbPath ?? (chairId
    ? `/glb/${chairId.endsWith('.glb') ? chairId : `${chairId}.glb`}`
    : '');
  if (!url) throw new Error('GlbChair: pass glbPath or chairId');
  const gltf = useGLTF(url) as any;

  const cloned = useMemo(() => {
    const root = gltf.scene.clone(true);
    // No shadow-casting on chair meshes; their meshes are heavy and the scene
    // renders dozens at once. Floor still casts ambient occlusion via bake.
    root.traverse((o: any) => { if (o.isMesh) { o.castShadow = false; o.receiveShadow = false; } });

    // Determine final scale.
    let s = scale;
    if (targetHeight != null) {
      const baseBox = new THREE.Box3().setFromObject(root);
      const baseH = Math.max(baseBox.max.y - baseBox.min.y, 0.001);
      s = targetHeight / baseH;
    }
    root.scale.setScalar(s);

    if (groundAlign) {
      root.updateMatrixWorld(true);
      const box = new THREE.Box3().setFromObject(root);
      const center = box.getCenter(new THREE.Vector3());
      root.position.x -= center.x;
      root.position.y -= box.min.y;
      root.position.z -= center.z;
    }
    return root;
  }, [gltf, groundAlign, scale, targetHeight]);

  return (
    <group position={position} rotation={[0, rotationY, 0]}>
      <primitive object={cloned} />
    </group>
  );
}

export const CHAIR_VISUAL_SCALE = 2.5;

// Top-down play needs oversized silhouettes; native and procedural chairs are
// intentionally amplified so they read as the main characters from above.
export const CHAIR_TARGET_H = 1.2 * CHAIR_VISUAL_SCALE;
export const CHAIR_STACK_PITCH = 0.7 * CHAIR_VISUAL_SCALE;
