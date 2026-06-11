import { create } from 'zustand';
import type {
  CameraPreset,
  LoadedModel,
  LoadStatus,
  PanelKey,
  RenderMode,
} from './types';

export interface LoadedModelEntry {
  id: string;
  name: string;
  visible: boolean;
  model: LoadedModel;
}

/** Per-part articulation: rotation in degrees, position offset in model units. */
export interface PartTransform {
  rotation: [number, number, number];
  position: [number, number, number];
}

const ZERO_TRANSFORM: PartTransform = { rotation: [0, 0, 0], position: [0, 0, 0] };

function transformFor(transforms: Record<string, PartTransform>, uuid: string): PartTransform {
  const current = transforms[uuid] ?? ZERO_TRANSFORM;
  return { rotation: [...current.rotation] as [number, number, number], position: [...current.position] as [number, number, number] };
}

/* Layout persistence — panel widths + collapsed state survive reloads. */
const LAYOUT_KEY = 'cadv.layout.v1';
const PANEL_HARD_MIN = 168; // absolute guard; the real (content-driven) floor is enforced in the UI
const PANEL_HARD_MAX = 720;
const DEFAULT_LEFT = 252;
const DEFAULT_RIGHT = 268;

function clampWidth(w: number) {
  if (!Number.isFinite(w)) return DEFAULT_LEFT;
  return Math.min(PANEL_HARD_MAX, Math.max(PANEL_HARD_MIN, Math.round(w)));
}

interface StoredLayout {
  leftWidth?: number;
  rightWidth?: number;
  scene?: boolean;
  properties?: boolean;
}

function loadLayout(): StoredLayout {
  try {
    if (typeof localStorage === 'undefined') return {};
    return JSON.parse(localStorage.getItem(LAYOUT_KEY) ?? '{}') as StoredLayout;
  } catch {
    return {};
  }
}

const saved = loadLayout();

interface ViewerState {
  models: LoadedModelEntry[];
  activeModelId: string | null;
  renderMode: RenderMode;
  cameraPreset: CameraPreset;
  panelState: Record<PanelKey, boolean>;
  leftWidth: number;
  rightWidth: number;
  loadStatus: LoadStatus;
  viewRevision: number;
  fitRevision: number;
  resetRevision: number;
  activePartUuid: string | null;
  partTransforms: Record<string, PartTransform>;
  partColors: Record<string, string>;
  hiddenParts: Record<string, true>;
  autoSpin: Record<string, { axis: 0 | 1 | 2; speed: number }>;
  explode: Record<string, number>;
  showOverlaps: boolean;
  overlapCount: number;
  overlapFrozen: boolean;
  animationPlaying: boolean;
  animationClipIndex: number;
  animationSpeed: number;
  addModel: (model: LoadedModel) => LoadedModelEntry;
  clearModels: () => void;
  toggleModelVisibility: (id: string) => void;
  isolateModel: (id: string) => void;
  removeModel: (id: string) => void;
  setActiveModel: (id: string) => void;
  setRenderMode: (mode: RenderMode) => void;
  setCameraPreset: (preset: CameraPreset) => void;
  togglePanel: (panel: PanelKey) => void;
  setLeftWidth: (width: number) => void;
  setRightWidth: (width: number) => void;
  setLoadStatus: (status: LoadStatus) => void;
  requestFit: () => void;
  requestReset: () => void;
  setActivePart: (uuid: string | null) => void;
  setPartRotation: (uuid: string, axis: 0 | 1 | 2, value: number) => void;
  setPartPosition: (uuid: string, axis: 0 | 1 | 2, value: number) => void;
  resetPart: (uuid: string) => void;
  setPartColor: (uuid: string, color: string) => void;
  clearPartColor: (uuid: string) => void;
  togglePartVisibility: (uuid: string) => void;
  isolatePart: (keepUuids: string[], modelUuids: string[]) => void;
  showAllParts: (modelUuids: string[]) => void;
  toggleAutoSpin: (uuid: string) => void;
  setAutoSpinAxis: (uuid: string, axis: 0 | 1 | 2) => void;
  setAutoSpinSpeed: (uuid: string, speed: number) => void;
  setExplode: (modelId: string, factor: number) => void;
  setShowOverlaps: (show: boolean) => void;
  setOverlapCount: (count: number) => void;
  setOverlapFrozen: (frozen: boolean) => void;
  clearArticulation: (modelId: string, uuids: string[]) => void;
  setAnimationPlaying: (playing: boolean) => void;
  setAnimationClipIndex: (index: number) => void;
  setAnimationSpeed: (speed: number) => void;
}

let nextModelId = 1;

function uniqueModelName(baseName: string, models: LoadedModelEntry[]) {
  const base = baseName.trim() || 'Untitled model';
  const existingNames = new Set(models.map((entry) => entry.name));
  if (!existingNames.has(base)) return base;

  let suffix = 2;
  while (existingNames.has(`${base} ${suffix}`)) suffix += 1;
  return `${base} ${suffix}`;
}

function offsetForModel(model: LoadedModel, models: LoadedModelEntry[]) {
  if (models.length === 0) return 0;
  const widestSpan = Math.max(model.metadata.size[0], ...models.map((entry) => entry.model.metadata.size[0]), 1.6);
  return models.length * widestSpan * 1.25;
}

export const useViewerStore = create<ViewerState>((set) => ({
  models: [],
  activeModelId: null,
  renderMode: 'shaded',
  cameraPreset: 'isometric',
  panelState: { scene: saved.scene ?? true, properties: saved.properties ?? true },
  leftWidth: clampWidth(saved.leftWidth ?? DEFAULT_LEFT),
  rightWidth: clampWidth(saved.rightWidth ?? DEFAULT_RIGHT),
  loadStatus: { state: 'idle', message: 'Load a bundled STEP sample or choose a STEP/STP, STL, OBJ, glTF, or GLB file.' },
  viewRevision: 0,
  fitRevision: 0,
  resetRevision: 0,
  activePartUuid: null,
  partTransforms: {},
  partColors: {},
  hiddenParts: {},
  autoSpin: {},
  explode: {},
  showOverlaps: false,
  overlapCount: 0,
  overlapFrozen: false,
  animationPlaying: false,
  animationClipIndex: 0,
  animationSpeed: 1,
  addModel: (model) => {
    const id = `model-${nextModelId++}`;
    let addedEntry: LoadedModelEntry | null = null;

    set((state) => {
      const name = uniqueModelName(model.metadata.name, state.models);
      model.group.position.setX(offsetForModel(model, state.models));
      addedEntry = { id, name, visible: true, model };
      return {
        models: [...state.models, addedEntry],
        activeModelId: id,
        activePartUuid: null,
        animationPlaying: false,
        animationClipIndex: 0,
        showOverlaps: false,
        overlapCount: 0,
        overlapFrozen: false,
      };
    });

    return addedEntry ?? { id, name: model.metadata.name, visible: true, model };
  },
  clearModels: () => set((state) => ({
    models: [],
    activeModelId: null,
    activePartUuid: null,
    partTransforms: {},
    partColors: {},
    hiddenParts: {},
    autoSpin: {},
    explode: {},
    showOverlaps: false,
    overlapCount: 0,
    overlapFrozen: false,
    animationPlaying: false,
    animationClipIndex: 0,
    fitRevision: state.fitRevision + 1,
  })),
  toggleModelVisibility: (id) => set((state) => {
    const target = state.models.find((entry) => entry.id === id);
    if (!target) return {};

    const willBeVisible = !target.visible;
    const models = state.models.map((entry) => (entry.id === id ? { ...entry, visible: willBeVisible } : entry));
    const activeStillVisible = models.some((entry) => entry.id === state.activeModelId && entry.visible);
    const activeModelId = activeStillVisible ? state.activeModelId : models.find((entry) => entry.visible)?.id ?? null;

    return { models, activeModelId, fitRevision: state.fitRevision + 1 };
  }),
  isolateModel: (id) => set((state) => {
    const target = state.models.find((entry) => entry.id === id);
    if (!target) return {};

    // Toggle: if this model is already the only visible one, un-isolate (show all).
    const others = state.models.filter((entry) => entry.id !== id);
    const isIsolated = target.visible && others.length > 0 && others.every((entry) => !entry.visible);
    if (isIsolated) {
      return {
        models: state.models.map((entry) => ({ ...entry, visible: true })),
        fitRevision: state.fitRevision + 1,
      };
    }

    return {
      models: state.models.map((entry) => ({ ...entry, visible: entry.id === id })),
      activeModelId: id,
      fitRevision: state.fitRevision + 1,
    };
  }),
  removeModel: (id) => set((state) => {
    const models = state.models.filter((entry) => entry.id !== id);
    const activeStillVisible = models.some((entry) => entry.id === state.activeModelId && entry.visible);
    const activeModelId = activeStillVisible ? state.activeModelId : models.find((entry) => entry.visible)?.id ?? null;
    const explode = { ...state.explode };
    delete explode[id];
    return { models, activeModelId, explode, activePartUuid: null, animationPlaying: false, showOverlaps: false, overlapCount: 0, overlapFrozen: false, fitRevision: state.fitRevision + 1 };
  }),
  setActiveModel: (id) => set((state) => (
    state.models.some((entry) => entry.id === id && entry.visible)
      ? { activeModelId: id, activePartUuid: null, animationPlaying: false, animationClipIndex: 0, showOverlaps: false, overlapCount: 0, overlapFrozen: false, fitRevision: state.fitRevision + 1 }
      : {}
  )),
  setRenderMode: (renderMode) => set({ renderMode }),
  setCameraPreset: (cameraPreset) => set((state) => ({ cameraPreset, viewRevision: state.viewRevision + 1 })),
  togglePanel: (panel) => set((state) => ({ panelState: { ...state.panelState, [panel]: !state.panelState[panel] } })),
  setLeftWidth: (width) => set({ leftWidth: clampWidth(width) }),
  setRightWidth: (width) => set({ rightWidth: clampWidth(width) }),
  setLoadStatus: (loadStatus) => set({ loadStatus }),
  requestFit: () => set((state) => ({ fitRevision: state.fitRevision + 1 })),
  requestReset: () => set((state) => ({ cameraPreset: 'isometric', viewRevision: state.viewRevision + 1, resetRevision: state.resetRevision + 1 })),
  setActivePart: (activePartUuid) => set({ activePartUuid }),
  setPartRotation: (uuid, axis, value) => set((state) => {
    const next = transformFor(state.partTransforms, uuid);
    next.rotation[axis] = value;
    return { partTransforms: { ...state.partTransforms, [uuid]: next } };
  }),
  setPartPosition: (uuid, axis, value) => set((state) => {
    const next = transformFor(state.partTransforms, uuid);
    next.position[axis] = value;
    return { partTransforms: { ...state.partTransforms, [uuid]: next } };
  }),
  resetPart: (uuid) => set((state) => {
    if (!state.partTransforms[uuid]) return {};
    const partTransforms = { ...state.partTransforms };
    delete partTransforms[uuid];
    return { partTransforms };
  }),
  setPartColor: (uuid, color) => set((state) => ({ partColors: { ...state.partColors, [uuid]: color } })),
  clearPartColor: (uuid) => set((state) => {
    if (!state.partColors[uuid]) return {};
    const partColors = { ...state.partColors };
    delete partColors[uuid];
    return { partColors };
  }),
  togglePartVisibility: (uuid) => set((state) => {
    const hiddenParts = { ...state.hiddenParts };
    if (hiddenParts[uuid]) delete hiddenParts[uuid];
    else hiddenParts[uuid] = true;
    return { hiddenParts };
  }),
  // Isolate the target's visibility scope (itself + its lineage/subtree, supplied
  // as keepUuids) within one model. Toggles: if already isolated to exactly this
  // scope, reveal every part of the model again.
  isolatePart: (keepUuids, modelUuids) => set((state) => {
    const keep = new Set(keepUuids);
    const isolated = modelUuids.some((u) => state.hiddenParts[u])
      && modelUuids.every((u) => Boolean(state.hiddenParts[u]) === !keep.has(u));
    const hiddenParts = { ...state.hiddenParts };
    modelUuids.forEach((u) => { delete hiddenParts[u]; });
    if (!isolated) modelUuids.forEach((u) => { if (!keep.has(u)) hiddenParts[u] = true; });
    return { hiddenParts };
  }),
  showAllParts: (modelUuids) => set((state) => {
    const hiddenParts = { ...state.hiddenParts };
    modelUuids.forEach((u) => { delete hiddenParts[u]; });
    return { hiddenParts };
  }),
  toggleAutoSpin: (uuid) => set((state) => {
    const autoSpin = { ...state.autoSpin };
    if (autoSpin[uuid]) delete autoSpin[uuid];
    else autoSpin[uuid] = { axis: 1, speed: 1 };
    return { autoSpin };
  }),
  setAutoSpinAxis: (uuid, axis) => set((state) => {
    const current = state.autoSpin[uuid];
    if (!current) return {};
    return { autoSpin: { ...state.autoSpin, [uuid]: { ...current, axis } } };
  }),
  setAutoSpinSpeed: (uuid, speed) => set((state) => {
    const current = state.autoSpin[uuid];
    if (!current) return {};
    return { autoSpin: { ...state.autoSpin, [uuid]: { ...current, speed } } };
  }),
  setExplode: (modelId, factor) => set((state) => ({ explode: { ...state.explode, [modelId]: factor } })),
  setShowOverlaps: (showOverlaps) => set({ showOverlaps, ...(showOverlaps ? {} : { overlapCount: 0, overlapFrozen: false }) }),
  setOverlapCount: (overlapCount) => set((state) => (state.overlapCount === overlapCount ? {} : { overlapCount })),
  setOverlapFrozen: (overlapFrozen) => set((state) => (state.overlapFrozen === overlapFrozen ? {} : { overlapFrozen })),
  clearArticulation: (modelId, uuids) => set((state) => {
    const partTransforms = { ...state.partTransforms };
    const partColors = { ...state.partColors };
    const autoSpin = { ...state.autoSpin };
    const hiddenParts = { ...state.hiddenParts };
    uuids.forEach((uuid) => {
      delete partTransforms[uuid];
      delete partColors[uuid];
      delete autoSpin[uuid];
      delete hiddenParts[uuid];
    });
    const explode = { ...state.explode };
    delete explode[modelId];
    return { partTransforms, partColors, autoSpin, hiddenParts, explode, activePartUuid: null, showOverlaps: false, overlapCount: 0 };
  }),
  setAnimationPlaying: (animationPlaying) => set({ animationPlaying }),
  setAnimationClipIndex: (animationClipIndex) => set({ animationClipIndex, animationPlaying: true }),
  setAnimationSpeed: (animationSpeed) => set({ animationSpeed }),
}));

/* Dev/diagnostic handle — lets tooling inspect store state without a UI hook. */
if (typeof window !== 'undefined') {
  (window as unknown as { __viewerStore?: typeof useViewerStore }).__viewerStore = useViewerStore;
}

/* Persist layout-affecting state only. */
if (typeof window !== 'undefined') {
  useViewerStore.subscribe((state, prev) => {
    if (state.leftWidth !== prev.leftWidth || state.rightWidth !== prev.rightWidth || state.panelState !== prev.panelState) {
      try {
        localStorage.setItem(LAYOUT_KEY, JSON.stringify({
          leftWidth: state.leftWidth,
          rightWidth: state.rightWidth,
          scene: state.panelState.scene,
          properties: state.panelState.properties,
        }));
      } catch {
        /* storage unavailable — ignore */
      }
    }
  });
}
