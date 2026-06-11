import * as THREE from 'three';
import type { CameraPreset } from './types';

const presetVectors: Record<CameraPreset, THREE.Vector3> = {
  top: new THREE.Vector3(0, 1, 0),
  bottom: new THREE.Vector3(0, -1, 0),
  front: new THREE.Vector3(0, 0, 1),
  back: new THREE.Vector3(0, 0, -1),
  left: new THREE.Vector3(-1, 0, 0),
  right: new THREE.Vector3(1, 0, 0),
  isometric: new THREE.Vector3(1, 1, 1),
};

const fallbackBox = new THREE.Box3(new THREE.Vector3(-2, -2, -2), new THREE.Vector3(2, 2, 2));

type CameraControls = { target: THREE.Vector3; update: () => void };

export const cameraPresets = [
  { id: 'top', label: 'Top' },
  { id: 'bottom', label: 'Bottom' },
  { id: 'front', label: 'Front' },
  { id: 'back', label: 'Back' },
  { id: 'left', label: 'Left' },
  { id: 'right', label: 'Right' },
  { id: 'isometric', label: 'Isometric' },
] as const;

export function applyCameraPreset(
  camera: THREE.OrthographicCamera,
  controls: CameraControls | null,
  fitObject: THREE.Object3D | null,
  preset: CameraPreset,
  aspect = 1,
  focusObject: THREE.Object3D | null = fitObject,
) {
  const fitBox = boundingBoxFor(fitObject);
  const focusCenter = centerFor(focusObject, fitBox);
  const direction = presetVectors[preset].clone().normalize();
  const distance = Math.max(radiusFromCenter(fitBox, focusCenter) * 2.8, 6);

  camera.up.set(0, 1, 0);
  if (preset === 'top' || preset === 'bottom') {
    camera.up.set(0, 0, preset === 'top' ? -1 : 1);
  }

  camera.position.copy(focusCenter).add(direction.multiplyScalar(distance));
  controls?.target.copy(focusCenter);
  camera.lookAt(focusCenter);
  camera.updateMatrixWorld(true);
  fitOrthographicCamera(camera, fitObject, aspect, focusObject, controls);
}

export function fitOrthographicCamera(
  camera: THREE.OrthographicCamera,
  fitObject: THREE.Object3D | null,
  aspect = 1,
  focusObject: THREE.Object3D | null = fitObject,
  controls: CameraControls | null = null,
) {
  const fitBox = boundingBoxFor(fitObject);
  const focusCenter = centerFor(focusObject, fitBox);
  const radius = radiusFromCenter(fitBox, focusCenter);
  const distance = Math.max(radius * 2.8, 6);
  const viewOffset = cameraOffsetDirection(camera, focusCenter, controls);

  camera.zoom = 1;
  camera.position.copy(focusCenter).add(viewOffset.multiplyScalar(distance));
  controls?.target.copy(focusCenter);
  camera.lookAt(focusCenter);
  camera.updateMatrixWorld(true);

  const corners = boxCorners(fitBox).map((corner) => camera.worldToLocal(corner.clone()));
  const padding = Math.max(radius * 0.12, 0.2);
  const safeAspect = Number.isFinite(aspect) && aspect > 0 ? aspect : 1;

  let halfWidth = 0.75;
  let halfHeight = 0.75;
  let maxDepth = 1;

  corners.forEach((corner) => {
    halfWidth = Math.max(halfWidth, Math.abs(corner.x));
    halfHeight = Math.max(halfHeight, Math.abs(corner.y));
    maxDepth = Math.max(maxDepth, -corner.z);
  });

  halfWidth += padding;
  halfHeight += padding;

  if (halfWidth / halfHeight < safeAspect) {
    halfWidth = halfHeight * safeAspect;
  } else {
    halfHeight = halfWidth / safeAspect;
  }

  camera.left = -halfWidth;
  camera.right = halfWidth;
  camera.top = halfHeight;
  camera.bottom = -halfHeight;
  camera.near = 0.01;
  camera.far = Math.max(1000, maxDepth + Math.max(radius * 2, 10), distance + radius * 3);
  camera.updateProjectionMatrix();
  controls?.update();
}

export function boundingSphereFor(object: THREE.Object3D | null) {
  const sphere = new THREE.Sphere();
  boundingBoxFor(object).getBoundingSphere(sphere);
  sphere.radius = Math.max(sphere.radius, 1);
  return sphere;
}

function boundingBoxFor(object: THREE.Object3D | null) {
  if (!object) {
    return fallbackBox.clone();
  }

  object.updateWorldMatrix(true, true);
  const box = new THREE.Box3().setFromObject(object);
  return box.isEmpty() ? fallbackBox.clone() : box;
}

function centerFor(object: THREE.Object3D | null, fallback: THREE.Box3) {
  if (!object) {
    return fallback.getCenter(new THREE.Vector3());
  }

  const box = boundingBoxFor(object);
  return (box.isEmpty() ? fallback : box).getCenter(new THREE.Vector3());
}

function radiusFromCenter(box: THREE.Box3, center: THREE.Vector3) {
  return Math.max(...boxCorners(box).map((corner) => corner.distanceTo(center)), 1);
}

function cameraOffsetDirection(camera: THREE.OrthographicCamera, focusCenter: THREE.Vector3, controls: CameraControls | null) {
  const fromControlsTarget = controls ? camera.position.clone().sub(controls.target) : new THREE.Vector3();
  if (fromControlsTarget.lengthSq() > 0.000001) {
    return fromControlsTarget.normalize();
  }

  const fromFocus = camera.position.clone().sub(focusCenter);
  if (fromFocus.lengthSq() > 0.000001) {
    return fromFocus.normalize();
  }

  return presetVectors.isometric.clone().normalize();
}

function boxCorners(box: THREE.Box3) {
  const { min, max } = box;
  return [
    new THREE.Vector3(min.x, min.y, min.z),
    new THREE.Vector3(min.x, min.y, max.z),
    new THREE.Vector3(min.x, max.y, min.z),
    new THREE.Vector3(min.x, max.y, max.z),
    new THREE.Vector3(max.x, min.y, min.z),
    new THREE.Vector3(max.x, min.y, max.z),
    new THREE.Vector3(max.x, max.y, min.z),
    new THREE.Vector3(max.x, max.y, max.z),
  ];
}
