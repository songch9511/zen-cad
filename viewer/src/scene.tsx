import { useEffect } from 'react';
import * as THREE from 'three';
import { applyRenderMode } from './renderModes';
import { useViewerStore } from './store';
import type { LoadedModelEntry } from './store';
import type { RenderMode } from './types';

/**
 * 뷰어 전용 씬 렌더러 — 물리/시뮬레이션 제거 후 남은 순수 표시 경로.
 * Renders every visible model's group with the active render mode applied.
 */
export function ViewerScene({ models, renderMode }: { models: LoadedModelEntry[]; renderMode: RenderMode }) {
  const visibleModels = models.filter((entry) => entry.visible);
  return (
    <group>
      {visibleModels.map((entry) => (
        <ModelPrimitive key={entry.id} object={entry.model.group} renderMode={renderMode} />
      ))}
    </group>
  );
}

/**
 * The single source of truth for an object's *appearance*: render mode, per-part
 * colour, and per-part visibility — applied together, in a fixed order, in one
 * effect. Kinematics (transforms / spin / animation) live in Articulator and only
 * touch position/quaternion, so the two never race. applyRenderMode re-clones
 * materials and re-shows every mesh, so colour and hide must run after it.
 */
function ModelPrimitive({ object, renderMode }: { object: THREE.Group; renderMode: RenderMode }) {
  const partColors = useViewerStore((state) => state.partColors);
  const hiddenParts = useViewerStore((state) => state.hiddenParts);

  useEffect(() => {
    applyRenderMode(object, renderMode);

    const color = new THREE.Color();
    object.traverse((node) => {
      const hex = partColors[node.uuid];
      if (!hex) return;
      color.set(hex);
      node.traverse((child) => {
        const mesh = child as THREE.Mesh;
        if (!mesh.isMesh) return;
        const materials = Array.isArray(mesh.material) ? mesh.material : [mesh.material];
        materials.forEach((material) => {
          if (material && 'color' in material) (material as THREE.MeshStandardMaterial).color.copy(color);
        });
      });
    });

    object.traverse((node) => { if (hiddenParts[node.uuid]) node.visible = false; });
  }, [object, renderMode, partColors, hiddenParts]);

  return <primitive object={object} />;
}
