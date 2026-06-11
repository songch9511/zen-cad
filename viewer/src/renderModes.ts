import * as THREE from 'three';
import type { RenderMode } from './types';

const materialCache = new WeakMap<THREE.Mesh, THREE.Material | THREE.Material[]>();
const overlayCache = new WeakMap<THREE.Mesh, { feature: THREE.LineSegments; wire: THREE.LineSegments }>();
const pointsCache = new WeakMap<THREE.Mesh, THREE.Points>();

export function applyRenderMode(group: THREE.Group, mode: RenderMode) {
  group.traverse((child) => {
    if (!isMesh(child)) return;
    if (!materialCache.has(child)) {
      materialCache.set(child, cloneMaterial(child.material));
    }

    clearAuxiliary(child);

    if (mode === 'shaded') {
      child.visible = true;
      child.material = cloneMaterial(materialCache.get(child)!);
      setWireframe(child.material, false);
      setDoubleSided(child.material, true);
      return;
    }

    if (mode === 'wireframe') {
      child.visible = true;
      // Colourless body: write neither colour nor depth, so only CAD-style
      // feature/object edges are visible, not mesh tessellation diagonals.
      child.material = new THREE.MeshBasicMaterial({
        colorWrite: false,
        depthWrite: false,
        side: THREE.DoubleSide,
      });
      const overlay = getFeatureOverlay(child);
      overlay.visible = true;
      return;
    }

    if (mode === 'overlay') {
      child.visible = true;
      child.material = cloneMaterial(materialCache.get(child)!);
      setWireframe(child.material, false);
      setDoubleSided(child.material, true);
      setSurfaceOffset(child.material, true);
      const overlay = getFeatureOverlay(child);
      overlay.visible = true;
      return;
    }

    if (mode === 'xray') {
      child.visible = true;
      child.material = new THREE.MeshStandardMaterial({
        color: '#7f8b9b',
        emissive: '#ffffff',
        emissiveIntensity: 0,
        transparent: true,
        opacity: 0.36,
        depthWrite: false,
        roughness: 0.38,
        metalness: 0,
        side: THREE.DoubleSide,
      });
      const overlay = getFeatureOverlay(child);
      overlay.visible = true;
      return;
    }

    if (mode === 'normals') {
      child.visible = true;
      child.material = new THREE.MeshNormalMaterial({ flatShading: true, side: THREE.DoubleSide });
      return;
    }

    if (mode === 'points') {
      child.visible = true;
      child.material = new THREE.MeshBasicMaterial({
        color: '#f97316',
        transparent: true,
        opacity: 0.18,
        depthWrite: false,
        side: THREE.DoubleSide,
      });
      const points = getPoints(child);
      points.visible = true;
    }
  });
}

function clearAuxiliary(mesh: THREE.Mesh) {
  const overlays = overlayCache.get(mesh);
  if (overlays) {
    overlays.feature.visible = false;
    overlays.wire.visible = false;
  }
  const points = pointsCache.get(mesh);
  if (points) points.visible = false;
  mesh.visible = true;
}

function getFeatureOverlay(mesh: THREE.Mesh) {
  return getOverlays(mesh).feature;
}

function getWireOverlay(mesh: THREE.Mesh) {
  return getOverlays(mesh).wire;
}

function getOverlays(mesh: THREE.Mesh) {
  const cached = overlayCache.get(mesh);
  if (cached) return cached;

  const positionOnlyGeometry = createPositionOnlyGeometry(mesh.geometry);
  const featureEdges = new THREE.EdgesGeometry(positionOnlyGeometry, 24);
  positionOnlyGeometry.dispose();
  const feature = new THREE.LineSegments(featureEdges, new THREE.LineBasicMaterial({
    color: '#111113',
    transparent: false,
    depthTest: true,
    depthWrite: false,
  }));
  feature.name = `${mesh.name || 'mesh'} feature edges`;
  feature.visible = false;
  feature.renderOrder = 5;

  const wireEdges = new THREE.WireframeGeometry(mesh.geometry);
  const wire = new THREE.LineSegments(wireEdges, new THREE.LineBasicMaterial({
    color: '#202124',
    transparent: true,
    opacity: 0.88,
    depthTest: true,
    depthWrite: false,
  }));
  wire.name = `${mesh.name || 'mesh'} wire overlay`;
  wire.visible = false;
  wire.renderOrder = 4;

  mesh.add(feature);
  mesh.add(wire);
  const overlays = { feature, wire };
  overlayCache.set(mesh, overlays);
  return overlays;
}

function getPoints(mesh: THREE.Mesh) {
  const cached = pointsCache.get(mesh);
  if (cached) return cached;

  const points = new THREE.Points(
    mesh.geometry,
    new THREE.PointsMaterial({ color: '#f97316', size: 4, sizeAttenuation: false }),
  );
  points.name = `${mesh.name || 'mesh'} points`;
  points.renderOrder = 3;
  mesh.add(points);
  pointsCache.set(mesh, points);
  return points;
}

function createPositionOnlyGeometry(source: THREE.BufferGeometry, tolerance = 1e-5) {
  const position = source.getAttribute('position');
  const index = source.getIndex();
  const geometry = new THREE.BufferGeometry();

  if (!position) return source.clone();

  const positions: number[] = [];
  const indices: number[] = [];
  const vertexByPosition = new Map<string, number>();

  const remapVertex = (sourceIndex: number) => {
    const x = position.getX(sourceIndex);
    const y = position.getY(sourceIndex);
    const z = position.getZ(sourceIndex);
    const key = [
      Math.round(x / tolerance),
      Math.round(y / tolerance),
      Math.round(z / tolerance),
    ].join(':');
    const existing = vertexByPosition.get(key);
    if (existing !== undefined) return existing;

    const next = positions.length / 3;
    vertexByPosition.set(key, next);
    positions.push(x, y, z);
    return next;
  };

  const readIndex = (offset: number) => (index ? index.getX(offset) : offset);
  const count = index ? index.count : position.count;

  for (let offset = 0; offset + 2 < count; offset += 3) {
    const a = remapVertex(readIndex(offset));
    const b = remapVertex(readIndex(offset + 1));
    const c = remapVertex(readIndex(offset + 2));
    if (a !== b && b !== c && a !== c) indices.push(a, b, c);
  }

  geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  geometry.setIndex(indices);
  return geometry;
}

function cloneMaterial(material: THREE.Material | THREE.Material[]): THREE.Material | THREE.Material[] {
  return Array.isArray(material) ? material.map((item) => item.clone()) : material.clone();
}

function setWireframe(material: THREE.Material | THREE.Material[], wireframe: boolean) {
  const materials = Array.isArray(material) ? material : [material];
  materials.forEach((item) => {
    if ('wireframe' in item) {
      item.wireframe = wireframe;
    }
  });
}

function setDoubleSided(material: THREE.Material | THREE.Material[], enabled: boolean) {
  const materials = Array.isArray(material) ? material : [material];
  materials.forEach((item) => {
    item.side = enabled ? THREE.DoubleSide : THREE.FrontSide;
    item.needsUpdate = true;
  });
}

function setSurfaceOffset(material: THREE.Material | THREE.Material[], enabled: boolean) {
  const materials = Array.isArray(material) ? material : [material];
  materials.forEach((item) => {
    item.polygonOffset = enabled;
    item.polygonOffsetFactor = enabled ? 1 : 0;
    item.polygonOffsetUnits = enabled ? 1 : 0;
    item.needsUpdate = true;
  });
}

function isMesh(value: THREE.Object3D): value is THREE.Mesh<THREE.BufferGeometry, THREE.Material | THREE.Material[]> {
  return (value as THREE.Mesh).isMesh === true;
}
