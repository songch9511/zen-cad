import type * as THREE from 'three';

export type VectorTuple = [number, number, number];

export type RenderMode = 'shaded' | 'wireframe' | 'overlay' | 'xray' | 'normals' | 'points';

export type CameraPreset = 'top' | 'bottom' | 'front' | 'back' | 'left' | 'right' | 'isometric';

export type PanelKey = 'scene' | 'properties';

export type LoadStatus =
  | { state: 'idle'; message: string }
  | { state: 'loading'; message: string }
  | { state: 'ready'; message: string }
  | { state: 'error'; message: string };

export interface ModelMetadata {
  name: string;
  format: 'STEP/STP' | 'STL' | 'OBJ' | 'glTF/GLB';
  source: 'sample' | 'file' | 'url';
  meshCount: number;
  vertexCount: number;
  size: VectorTuple;
}

export interface LoadedModel {
  group: THREE.Group;
  metadata: ModelMetadata;
  animations?: THREE.AnimationClip[];
}
