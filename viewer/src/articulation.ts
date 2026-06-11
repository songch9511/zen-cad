import * as THREE from 'three';
import { MeshBVH } from 'three-mesh-bvh';
import { Brush, Evaluator, INTERSECTION } from 'three-bvh-csg';

/**
 * 운동학(파트 변환) 헬퍼 — 물리 없이 노드 트랜스폼만 다룬다.
 * Walks a loaded model's node graph into a flat, depth-tagged part list and
 * records each node's base (un-articulated) transform so slider deltas can be
 * applied relative to it. Top-level parts also get an explode direction.
 */

export interface PartNode {
  uuid: string;
  name: string;
  depth: number;
  topLevel: boolean;
  node: THREE.Object3D;
}

export interface PartBase {
  position: THREE.Vector3;
  quaternion: THREE.Quaternion;
  explodeVec: THREE.Vector3;
}

export interface ArticulationContext {
  group: THREE.Group;
  parts: PartNode[];
  bases: Map<string, PartBase>;
}

const MAX_PARTS = 300;
const ZERO = new THREE.Vector3();

function hasMeshDescendant(node: THREE.Object3D): boolean {
  let found = false;
  node.traverse((child) => {
    if (child !== node && (child as THREE.Mesh).isMesh === true) found = true;
  });
  return found;
}

export function collectParts(group: THREE.Group): ArticulationContext {
  const parts: PartNode[] = [];
  const bases = new Map<string, PartBase>();

  const assemblyBox = new THREE.Box3().setFromObject(group);
  const assemblyCenter = assemblyBox.isEmpty() ? new THREE.Vector3() : assemblyBox.getCenter(new THREE.Vector3());
  const topLevel = new Set<THREE.Object3D>(group.children);

  const visit = (node: THREE.Object3D, depth: number) => {
    if (parts.length >= MAX_PARTS) return;
    const isMesh = (node as THREE.Mesh).isMesh === true;
    const articulable = depth > 0 && (isMesh || hasMeshDescendant(node));

    if (articulable) {
      const isTop = topLevel.has(node);
      let explodeVec = ZERO.clone();
      if (isTop) {
        const box = new THREE.Box3().setFromObject(node);
        if (!box.isEmpty()) explodeVec = box.getCenter(new THREE.Vector3()).sub(assemblyCenter);
      }
      parts.push({ uuid: node.uuid, name: node.name || `Part ${parts.length + 1}`, depth: depth - 1, topLevel: isTop, node });
      bases.set(node.uuid, { position: node.position.clone(), quaternion: node.quaternion.clone(), explodeVec });
    }

    node.children.forEach((child) => visit(child, depth + 1));
  };

  visit(group, 0);
  return { group, parts, bases };
}

/**
 * Cache the articulation context per group so base transforms are captured once
 * (at first access, before any articulation) and stay stable for the group's
 * lifetime — re-deriving after a slider moved would poison the base pose.
 */
const articulationCache = new WeakMap<THREE.Group, ArticulationContext>();

export function getArticulation(group: THREE.Group): ArticulationContext {
  const cached = articulationCache.get(group);
  if (cached) return cached;
  const context = collectParts(group);
  articulationCache.set(group, context);
  return context;
}

/** Largest bounding-box dimension — drives slider ranges and explode scale. */
export function modelSpan(size: readonly [number, number, number]): number {
  return Math.max(size[0], size[1], size[2], 0.001);
}

export interface OverlapResult {
  /** World-space boolean-intersection geometries to paint red. */
  geometries: THREE.BufferGeometry[];
  /** Number of top-level part pairs that interfere. */
  pairs: number;
}

// Beyond these limits a pair is still counted as interfering but its overlap
// volume is not computed — keeps dense / many-part assemblies responsive.
const CSG_TRIANGLE_CAP = 200000;
const CSG_EVAL_BUDGET = 64;

const _btoa = new THREE.Matrix4();

const bvhCache = new WeakMap<THREE.BufferGeometry, MeshBVH>();
const brushGeometryCache = new WeakMap<THREE.BufferGeometry, THREE.BufferGeometry>();

const evaluator = new Evaluator();
evaluator.attributes = ['position', 'normal'];
evaluator.useGroups = false;

function getBVH(geometry: THREE.BufferGeometry): MeshBVH {
  let bvh = bvhCache.get(geometry);
  if (!bvh) {
    bvh = new MeshBVH(geometry);
    bvhCache.set(geometry, bvh);
  }
  return bvh;
}

function meshesUnder(node: THREE.Object3D): THREE.Mesh[] {
  const meshes: THREE.Mesh[] = [];
  node.traverse((child) => {
    const mesh = child as THREE.Mesh;
    if (mesh.isMesh && (mesh.geometry as THREE.BufferGeometry)?.attributes?.position) meshes.push(mesh);
  });
  return meshes;
}

function triangleCount(geometry: THREE.BufferGeometry): number {
  return (geometry.index ? geometry.index.count : geometry.attributes.position.count) / 3;
}

/** Position + normal only — a clean, attribute-matched brush input for the CSG. */
function brushGeometryFor(geometry: THREE.BufferGeometry): THREE.BufferGeometry {
  let prepared = brushGeometryCache.get(geometry);
  if (prepared) return prepared;
  prepared = new THREE.BufferGeometry();
  prepared.setAttribute('position', geometry.attributes.position.clone());
  if (geometry.index) prepared.setIndex(geometry.index.clone());
  if (geometry.attributes.normal) prepared.setAttribute('normal', geometry.attributes.normal.clone());
  else prepared.computeVertexNormals();
  brushGeometryCache.set(geometry, prepared);
  return prepared;
}

function brushFor(mesh: THREE.Mesh): Brush {
  const brush = new Brush(brushGeometryFor(mesh.geometry as THREE.BufferGeometry));
  brush.matrixAutoUpdate = false;
  brush.matrix.copy(mesh.matrixWorld);
  brush.updateMatrixWorld(true);
  return brush;
}

/**
 * Mesh-level interference as a *volume*: for each pair of top-level parts whose
 * world AABBs overlap, boolean-intersect their meshes (three-bvh-csg) and return
 * the shared solids in world space — the real overlapping region, tighter than a
 * bounding box. A fast BVH surface test gates the boolean and keeps the pair
 * count correct even when the volume is skipped (dense pair / over budget) or the
 * boolean fails on a non-watertight mesh.
 */
export function computeOverlapVolumes(parts: PartNode[]): OverlapResult {
  const tops = parts.filter((part) => part.topLevel);
  const entries = tops.map((part) => {
    part.node.updateWorldMatrix(true, true);
    const meshes = meshesUnder(part.node);
    const box = new THREE.Box3().setFromObject(part.node);
    const tris = meshes.reduce((sum, mesh) => sum + triangleCount(mesh.geometry as THREE.BufferGeometry), 0);
    return { meshes, box, tris };
  });

  const geometries: THREE.BufferGeometry[] = [];
  let pairs = 0;
  let evals = 0;

  for (let i = 0; i < entries.length; i += 1) {
    if (entries[i].box.isEmpty() || entries[i].meshes.length === 0) continue;
    for (let j = i + 1; j < entries.length; j += 1) {
      if (entries[j].box.isEmpty() || entries[j].meshes.length === 0) continue;
      if (!entries[i].box.intersectsBox(entries[j].box)) continue;

      const heavy = entries[i].tris + entries[j].tris > CSG_TRIANGLE_CAP;
      let contributed = false;

      for (const meshA of entries[i].meshes) {
        for (const meshB of entries[j].meshes) {
          // Precise surface-touch test — gates the boolean and counts the pair.
          let touches = false;
          try {
            _btoa.copy(meshA.matrixWorld).invert().multiply(meshB.matrixWorld);
            touches = getBVH(meshA.geometry as THREE.BufferGeometry).intersectsGeometry(meshB.geometry as THREE.BufferGeometry, _btoa);
          } catch {
            touches = false;
          }
          if (!touches) continue;
          contributed = true;

          if (heavy || evals >= CSG_EVAL_BUDGET) continue;
          evals += 1;
          try {
            const result = evaluator.evaluate(brushFor(meshA), brushFor(meshB), INTERSECTION);
            const position = result.geometry?.attributes?.position;
            if (position && position.count > 0) geometries.push(result.geometry);
            else result.geometry?.dispose?.();
          } catch {
            /* boolean failed (e.g. non-watertight) — pair still counted, not painted */
          }
        }
      }

      if (contributed) pairs += 1;
    }
  }

  return { geometries, pairs };
}
