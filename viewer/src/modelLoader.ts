import * as THREE from 'three';
import occtImportJs from 'occt-import-js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { OBJLoader } from 'three/examples/jsm/loaders/OBJLoader.js';
import { STLLoader } from 'three/examples/jsm/loaders/STLLoader.js';
import type { LoadedModel, ModelMetadata } from './types';
import type { OcctImportMesh, OcctModule } from 'occt-import-js';

const supportedExtensions = ['stl', 'obj', 'gltf', 'glb', 'step', 'stp'];
const occtRuntimePath = '/vendor/occt/';
let occtModulePromise: Promise<OcctModule> | null = null;

export function isSupportedModelName(name: string) {
  return supportedExtensions.includes(extensionFromName(name));
}

export function supportedModelHint() {
  return 'Supported formats: STEP/STP, STL, OBJ, glTF, GLB.';
}

export async function loadModelFromFile(file: File): Promise<LoadedModel> {
  const extension = extensionFromName(file.name);

  if (!supportedExtensions.includes(extension)) {
    throw new Error(`Unsupported file type .${extension || 'unknown'}. ${supportedModelHint()}`);
  }

  if (isStepExtension(extension)) {
    const buffer = await file.arrayBuffer();
    const group = await loadStepGroup(new Uint8Array(buffer));
    return finalizeModel(group, file.name, formatFromExtension(extension), 'file');
  }

  const url = URL.createObjectURL(file);
  try {
    const { group, animations } = await loadGroupFromUrl(url, extension);
    return finalizeModel(group, file.name, formatFromExtension(extension), 'file', animations);
  } finally {
    URL.revokeObjectURL(url);
  }
}

export async function loadModelFromUrl(path: string, label: string, source: ModelMetadata['source'] = 'sample'): Promise<LoadedModel> {
  const extension = extensionFromName(path);
  if (isStepExtension(extension)) {
    const response = await fetch(path);
    if (!response.ok) {
      throw new Error(`Could not fetch STEP sample (${response.status}).`);
    }
    const group = await loadStepGroup(new Uint8Array(await response.arrayBuffer()));
    return finalizeModel(group, label, formatFromExtension(extension), source);
  }
  const { group, animations } = await loadGroupFromUrl(path, extension);
  return finalizeModel(group, label, formatFromExtension(extension), source, animations);
}

interface LoadedGroup {
  group: THREE.Group;
  animations: THREE.AnimationClip[];
}

function loadGroupFromUrl(url: string, extension: string): Promise<LoadedGroup> {
  if (extension === 'stl') {
    return new Promise((resolve, reject) => {
      new STLLoader().load(
        url,
        (geometry) => {
          geometry.computeVertexNormals();
          const material = new THREE.MeshStandardMaterial({ color: '#9db7d7', metalness: 0.08, roughness: 0.54 });
          const mesh = new THREE.Mesh(geometry, material);
          mesh.name = 'STL mesh';
          const group = new THREE.Group();
          group.add(mesh);
          resolve({ group, animations: [] });
        },
        undefined,
        () => reject(new Error('Could not load STL geometry.')),
      );
    });
  }

  if (extension === 'obj') {
    return new Promise((resolve, reject) => {
      new OBJLoader().load(
        url,
        (object) => resolve({ group: object, animations: [] }),
        undefined,
        () => reject(new Error('Could not load OBJ model.')),
      );
    });
  }

  if (extension === 'gltf' || extension === 'glb') {
    return new Promise((resolve, reject) => {
      new GLTFLoader().load(
        url,
        (gltf) => resolve({ group: gltf.scene as unknown as THREE.Group, animations: gltf.animations ?? [] }),
        undefined,
        () => reject(new Error('Could not load glTF/GLB scene.')),
      );
    });
  }

  return Promise.reject(new Error(`Unsupported file type .${extension || 'unknown'}. ${supportedModelHint()}`));
}

async function loadStepGroup(content: Uint8Array) {
  const occt = await getOcctModule();
  // Finer deflection => denser tessellation: smoother curved surfaces (and
  // smoother overlap booleans) at the cost of more triangles. Halve the linear
  // and roughly halve the angular deflection vs OCCT-ish coarse defaults.
  const result = occt.ReadStepFile(content, {
    linearUnit: 'millimeter',
    linearDeflectionType: 'bounding_box_ratio',
    linearDeflection: 0.0004,
    angularDeflection: 0.18,
  });

  if (!result.success || !result.meshes?.length) {
    throw new Error(result.error || 'Could not tessellate STEP geometry. Check that the file is a valid ISO-10303 STEP model.');
  }

  const group = new THREE.Group();
  group.name = 'STEP assembly';
  result.meshes.forEach((mesh, index) => {
    group.add(meshFromOcctMesh(mesh, index));
  });
  return group;
}

function getOcctModule() {
  occtModulePromise ??= occtImportJs({
    locateFile: (path: string) => `${occtRuntimePath}${path}`,
    print: () => undefined,
    printErr: (...args: unknown[]) => console.warn('[occt-import-js]', ...args),
  }).catch((error) => {
    occtModulePromise = null;
    throw new Error(`Could not initialize STEP import engine. ${error instanceof Error ? error.message : String(error)}`);
  });
  return occtModulePromise;
}

function meshFromOcctMesh(mesh: OcctImportMesh, index: number) {
  const geometry = new THREE.BufferGeometry();
  geometry.setAttribute('position', new THREE.Float32BufferAttribute(mesh.attributes.position.array, 3));
  if (mesh.attributes.normal?.array?.length) {
    geometry.setAttribute('normal', new THREE.Float32BufferAttribute(mesh.attributes.normal.array, 3));
  }
  if (mesh.index?.array?.length) {
    geometry.setIndex(mesh.index.array);
  }
  geometry.computeVertexNormals();
  geometry.computeBoundingBox();
  geometry.computeBoundingSphere();

  const neutralCadColor = new THREE.Color('#b9c0ca');
  const color = mesh.color
    ? new THREE.Color(mesh.color[0], mesh.color[1], mesh.color[2]).lerp(neutralCadColor, 0.78)
    : neutralCadColor;
  const material = new THREE.MeshStandardMaterial({ color, roughness: 0.42, metalness: 0.12 });
  const threeMesh = new THREE.Mesh(geometry, material);
  threeMesh.name = mesh.name || `STEP body ${index + 1}`;
  return threeMesh;
}

function finalizeModel(group: THREE.Group, name: string, format: ModelMetadata['format'], source: ModelMetadata['source'], animations: THREE.AnimationClip[] = []): LoadedModel {
  const prepared = group.clone(true);
  prepared.name = name;
  ensureMaterials(prepared);
  normalizeToOrigin(prepared);

  const box = new THREE.Box3().setFromObject(prepared);
  const sizeVector = box.getSize(new THREE.Vector3());
  let meshCount = 0;
  let vertexCount = 0;

  prepared.traverse((child) => {
    if (isMesh(child)) {
      meshCount += 1;
      const position = child.geometry.getAttribute('position');
      vertexCount += position ? position.count : 0;
    }
  });

  return {
    group: prepared,
    metadata: {
      name,
      format,
      source,
      meshCount,
      vertexCount,
      size: [sizeVector.x, sizeVector.y, sizeVector.z],
    },
    animations,
  };
}

function normalizeToOrigin(group: THREE.Group) {
  const box = new THREE.Box3().setFromObject(group);
  if (box.isEmpty()) {
    return;
  }
  const center = box.getCenter(new THREE.Vector3());
  group.position.sub(center);
}

function ensureMaterials(group: THREE.Group) {
  const palette = ['#9db7d7', '#d7b49d', '#a8d7a0', '#d7a0cf'];
  let meshIndex = 0;
  group.traverse((child) => {
    if (!isMesh(child)) {
      return;
    }
    child.name = child.name || `Mesh ${meshIndex + 1}`;
    const sourceMaterial = Array.isArray(child.material) ? child.material[0] : child.material;
    if (!sourceMaterial || !('color' in sourceMaterial)) {
      child.material = new THREE.MeshStandardMaterial({ color: palette[meshIndex % palette.length], roughness: 0.58, metalness: 0.05 });
    }
    child.castShadow = true;
    child.receiveShadow = true;
    meshIndex += 1;
  });
}

function extensionFromName(name: string) {
  return name.split(/[?#]/)[0].split('.').pop()?.toLowerCase() ?? '';
}

function isStepExtension(extension: string) {
  return extension === 'step' || extension === 'stp';
}

function formatFromExtension(extension: string): ModelMetadata['format'] {
  if (extension === 'stl') return 'STL';
  if (extension === 'obj') return 'OBJ';
  if (isStepExtension(extension)) return 'STEP/STP';
  return 'glTF/GLB';
}

function isMesh(value: THREE.Object3D): value is THREE.Mesh<THREE.BufferGeometry, THREE.Material | THREE.Material[]> {
  return (value as THREE.Mesh).isMesh === true;
}
