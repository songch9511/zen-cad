import { Suspense, useCallback, useEffect, useMemo, useRef, useState } from 'react';
import type { CSSProperties, DragEvent, FormEvent, KeyboardEvent as ReactKeyboardEvent, PointerEvent as ReactPointerEvent } from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import { GizmoHelper, GizmoViewport, OrbitControls } from '@react-three/drei';
import { EffectComposer, N8AO } from '@react-three/postprocessing';
import * as THREE from 'three';
import { cameraPresets, applyCameraPreset, fitOrthographicCamera } from './camera';
import { computeOverlapVolumes, getArticulation, modelSpan } from './articulation';
import type { ArticulationContext, PartNode } from './articulation';
import { isSupportedModelName, loadModelFromFile, loadModelFromUrl, supportedModelHint } from './modelLoader';
import { ViewerScene } from './scene';
import { sampleModels } from './samples';
import { useViewerStore } from './store';
import type { LoadedModelEntry } from './store';
import type { CameraPreset, RenderMode } from './types';

const acceptedModelTypes = '.step,.stp,.stl,.obj,.gltf,.glb,application/step,model/step,model/stl,model/obj,model/gltf+json,model/gltf-binary';
const RECENT_OPENS_KEY = 'cadv.recentOpens.v1';
const MAX_RECENT_OPENS = 6;

const renderModes: Array<{ id: RenderMode; label: string; railLabel: string; icon: IconName; description: string }> = [
  { id: 'shaded', label: 'Shaded', railLabel: 'Shaded', icon: 'shaded', description: 'Solid shaded model with original materials.' },
  { id: 'wireframe', label: 'Wireframe', railLabel: 'Wire', icon: 'wireframe', description: 'Edges-only wireframe material.' },
  { id: 'overlay', label: 'Shaded + Wire', railLabel: 'Overlay', icon: 'overlay', description: 'Shaded model with wire overlay.' },
  { id: 'xray', label: 'X-ray', railLabel: 'X-ray', icon: 'xray', description: 'Transparent x-ray material plus edges.' },
  { id: 'normals', label: 'Normals', railLabel: 'Normals', icon: 'normals', description: 'Normal-color flat inspection material.' },
  { id: 'points', label: 'Points', railLabel: 'Points', icon: 'points', description: 'Vertex cloud rendering.' },
];

const cameraIcons: Record<CameraPreset, IconName> = {
  top: 'top',
  bottom: 'bottom',
  front: 'front',
  back: 'back',
  left: 'left',
  right: 'right',
  isometric: 'isometric',
};

const axisLabels = ['X', 'Y', 'Z'] as const;

const PANEL_FALLBACK_MIN = 188;

// If one overlap recompute costs more than this, it is too heavy to run live
// during motion (it would jank the rotation) — overlap then freezes until rest.
const LIVE_OVERLAP_BUDGET_MS = 35;

interface RecentOpen {
  label: string;
  path: string;
  format: string;
}

function readRecentOpens(): RecentOpen[] {
  try {
    if (typeof localStorage === 'undefined') return [];
    const stored = JSON.parse(localStorage.getItem(RECENT_OPENS_KEY) ?? '[]') as RecentOpen[];
    if (!Array.isArray(stored)) return [];
    return stored
      .filter((item) => item && typeof item.label === 'string' && typeof item.path === 'string')
      .slice(0, MAX_RECENT_OPENS);
  } catch {
    return [];
  }
}

function writeRecentOpens(items: RecentOpen[]) {
  try {
    localStorage.setItem(RECENT_OPENS_KEY, JSON.stringify(items.slice(0, MAX_RECENT_OPENS)));
  } catch {
    /* localStorage may be unavailable in private or embedded contexts. */
  }
}

function labelFromModelPath(path: string) {
  const clean = path.trim().split(/[?#]/)[0];
  const rawName = clean.split('/').filter(Boolean).pop() ?? 'URL model';
  try {
    return decodeURIComponent(rawName);
  } catch {
    return rawName;
  }
}

function writeModelUrlParams(path: string, label: string) {
  const nextUrl = new URL(window.location.href);
  nextUrl.searchParams.set('model', path);
  nextUrl.searchParams.set('label', label);
  window.history.replaceState({}, '', `${nextUrl.pathname}${nextUrl.search}${nextUrl.hash}`);
}

function sampleMatchesCommand(sample: (typeof sampleModels)[number], query: string) {
  const normalized = query.trim().toLowerCase();
  if (!normalized) return false;
  return (
    sample.label.toLowerCase().includes(normalized) ||
    sample.path.toLowerCase().includes(normalized) ||
    sample.format.toLowerCase().includes(normalized)
  );
}

function isAncestorOf(maybeAncestor: THREE.Object3D, node: THREE.Object3D): boolean {
  let parent = node.parent;
  while (parent) {
    if (parent === maybeAncestor) return true;
    parent = parent.parent;
  }
  return false;
}

/**
 * UUIDs that must stay visible to isolate `target`: the part itself plus any
 * listed ancestor (hiding it would hide the target) or descendant (its own
 * sub-parts). For a flat STEP assembly this is just the target. Everything else
 * in the model is hidden.
 */
function isolationScope(target: PartNode, parts: PartNode[]): string[] {
  const keep = new Set<string>([target.uuid]);
  parts.forEach((part) => {
    if (part.uuid === target.uuid) return;
    if (isAncestorOf(part.node, target.node) || isAncestorOf(target.node, part.node)) keep.add(part.uuid);
  });
  return [...keep];
}

function panelMaxWidth() {
  if (typeof window === 'undefined') return 560;
  return Math.max(240, Math.min(600, Math.round(window.innerWidth * 0.42)));
}

function measurePanelFloor(panel: HTMLElement): number {
  const previous = panel.style.width;
  panel.style.width = '0px';
  const floor = panel.getBoundingClientRect().width;
  panel.style.width = previous;
  return Math.max(PANEL_FALLBACK_MIN, Math.ceil(floor));
}

function shouldUseAutomatedCanvas(): boolean {
  if (typeof window === 'undefined' || typeof navigator === 'undefined') return false;
  const params = new URLSearchParams(window.location.search);
  const realCanvasRequested = params.get('realCanvas') === '1' || params.get('evidence') === '1';
  return Boolean(navigator.webdriver) && !realCanvasRequested;
}

export default function App() {
  const inputRef = useRef<HTMLInputElement>(null);
  const commandInputRef = useRef<HTMLInputElement>(null);
  const urlLoadRef = useRef<string | null>(null);
  const [commandValue, setCommandValue] = useState('');
  const [explorerQuery, setExplorerQuery] = useState('');
  const [recentOpens, setRecentOpens] = useState<RecentOpen[]>(() => readRecentOpens());
  const models = useViewerStore((state) => state.models);
  const activeModelId = useViewerStore((state) => state.activeModelId);
  const renderMode = useViewerStore((state) => state.renderMode);
  const cameraPreset = useViewerStore((state) => state.cameraPreset);
  const panelState = useViewerStore((state) => state.panelState);
  const leftWidth = useViewerStore((state) => state.leftWidth);
  const rightWidth = useViewerStore((state) => state.rightWidth);
  const loadStatus = useViewerStore((state) => state.loadStatus);
  const addModel = useViewerStore((state) => state.addModel);
  const clearModels = useViewerStore((state) => state.clearModels);
  const setRenderMode = useViewerStore((state) => state.setRenderMode);
  const setCameraPreset = useViewerStore((state) => state.setCameraPreset);
  const togglePanel = useViewerStore((state) => state.togglePanel);
  const setLoadStatus = useViewerStore((state) => state.setLoadStatus);
  const requestFit = useViewerStore((state) => state.requestFit);
  const requestReset = useViewerStore((state) => state.requestReset);

  const activeModel = models.find((entry) => entry.id === activeModelId) ?? null;
  const articulation = useMemo(() => (activeModel ? getArticulation(activeModel.model.group) : null), [activeModel?.id]);
  const animations = activeModel?.model.animations ?? [];

  const rememberRecentOpen = useCallback((item: RecentOpen) => {
    setRecentOpens((current) => {
      const next = [
        item,
        ...current.filter((existing) => existing.path !== item.path),
      ].slice(0, MAX_RECENT_OPENS);
      writeRecentOpens(next);
      return next;
    });
  }, []);

  useEffect(() => {
    const onResize = () => {
      const max = panelMaxWidth();
      const state = useViewerStore.getState();
      if (state.leftWidth > max) state.setLeftWidth(max);
      if (state.rightWidth > max) state.setRightWidth(max);
    };
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const loadFile = useCallback(async (file: File) => {
    setLoadStatus({ state: 'loading', message: `Preparing ${file.name}… STEP files initialize the OpenCascade engine on first load.` });
    try {
      const loaded = await loadModelFromFile(file);
      addModel(loaded);
      setCameraPreset('isometric');
      requestFit();
      setLoadStatus({ state: 'ready', message: `Loaded ${loaded.metadata.name} · ${loaded.metadata.format} · ${loaded.metadata.meshCount} mesh${loaded.metadata.meshCount === 1 ? '' : 'es'}.` });
    } catch (error) {
      setLoadStatus({ state: 'error', message: error instanceof Error ? error.message : 'Could not load that model.' });
    }
  }, [addModel, requestFit, setCameraPreset, setLoadStatus]);

  const loadSample = useCallback(async (sample: (typeof sampleModels)[number]) => {
    setLoadStatus({ state: 'loading', message: sample.format === 'STEP' ? `Initializing STEP kernel and loading ${sample.label}…` : `Loading ${sample.label}…` });
    try {
      const loaded = await loadModelFromUrl(sample.path, sample.label);
      addModel(loaded);
      setCameraPreset('isometric');
      requestFit();
      rememberRecentOpen({ label: sample.label, path: sample.path, format: sample.format });
      writeModelUrlParams(sample.path, sample.label);
      setLoadStatus({ state: 'ready', message: `Loaded ${loaded.metadata.name} · ${loaded.metadata.format} · ${loaded.metadata.vertexCount.toLocaleString()} vertices.` });
    } catch (error) {
      setLoadStatus({ state: 'error', message: error instanceof Error ? error.message : `Could not load ${sample.label}.` });
    }
  }, [addModel, rememberRecentOpen, requestFit, setCameraPreset, setLoadStatus]);

  const loadPath = useCallback(async (path: string, label = labelFromModelPath(path)) => {
    const normalizedPath = path.trim();
    if (!normalizedPath) return;
    if (!isSupportedModelName(normalizedPath)) {
      setLoadStatus({ state: 'error', message: `Unsupported model path. ${supportedModelHint()}` });
      return;
    }

    setLoadStatus({ state: 'loading', message: `Loading ${label} from path…` });
    try {
      const loaded = await loadModelFromUrl(normalizedPath, label, 'url');
      addModel(loaded);
      setCameraPreset('isometric');
      requestFit();
      rememberRecentOpen({ label, path: normalizedPath, format: loaded.metadata.format });
      setCommandValue('');
      writeModelUrlParams(normalizedPath, label);

      setLoadStatus({ state: 'ready', message: `Loaded ${loaded.metadata.name} · ${loaded.metadata.format} · ${loaded.metadata.vertexCount.toLocaleString()} vertices.` });
    } catch (error) {
      setLoadStatus({ state: 'error', message: error instanceof Error ? error.message : `Could not load ${label}.` });
    }
  }, [addModel, rememberRecentOpen, requestFit, setCameraPreset, setLoadStatus]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const modelUrl = params.get('model') ?? params.get('url');
    if (!modelUrl || urlLoadRef.current === modelUrl) return;
    urlLoadRef.current = modelUrl;

    const label = params.get('label') ?? modelUrl.split('/').pop() ?? 'URL model';
    setLoadStatus({ state: 'loading', message: `Loading ${label} from URL…` });
    void loadModelFromUrl(modelUrl, label, 'url')
      .then((loaded) => {
        addModel(loaded);
        setCameraPreset('isometric');
        requestFit();
        rememberRecentOpen({ label, path: modelUrl, format: loaded.metadata.format });
        setLoadStatus({ state: 'ready', message: `Loaded ${loaded.metadata.name} · ${loaded.metadata.format} · ${loaded.metadata.vertexCount.toLocaleString()} vertices.` });
      })
      .catch((error) => {
        setLoadStatus({ state: 'error', message: error instanceof Error ? error.message : `Could not load ${label}.` });
      });
  }, [addModel, rememberRecentOpen, requestFit, setCameraPreset, setLoadStatus]);

  const handleFiles = useCallback((files: FileList | null) => {
    const [file] = Array.from(files ?? []);
    if (!file) return;
    void loadFile(file);
  }, [loadFile]);

  const handleDrop = useCallback((event: DragEvent<HTMLElement>) => {
    event.preventDefault();
    handleFiles(event.dataTransfer.files);
  }, [handleFiles]);

  const handleCommandSubmit = useCallback((event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const query = commandValue.trim();
    if (!query) {
      inputRef.current?.click();
      return;
    }

    const matchedSample = sampleModels.find((sample) => sampleMatchesCommand(sample, query));
    if (isSupportedModelName(query)) {
      void loadPath(query);
      return;
    }
    if (matchedSample) {
      setCommandValue('');
      void loadSample(matchedSample);
      return;
    }

    setExplorerQuery(query);
    setLoadStatus({ state: 'idle', message: `Filtered explorer for "${query}". Press Enter with a model URL or sample name to load.` });
  }, [commandValue, loadPath, loadSample, setLoadStatus]);

  const handleClearWorkspace = useCallback(() => {
    clearModels();
    setCommandValue('');
    setExplorerQuery('');
    urlLoadRef.current = null;
    const nextUrl = new URL(window.location.href);
    nextUrl.searchParams.delete('model');
    nextUrl.searchParams.delete('url');
    nextUrl.searchParams.delete('label');
    window.history.replaceState({}, '', `${nextUrl.pathname}${nextUrl.search}${nextUrl.hash}`);
    setLoadStatus({ state: 'idle', message: 'Workspace cleared. Load a bundled STEP sample, paste a model URL, or choose a local CAD file.' });
  }, [clearModels, setLoadStatus]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
        event.preventDefault();
        commandInputRef.current?.focus();
        commandInputRef.current?.select();
      }
      if (event.key === 'Escape' && document.activeElement === commandInputRef.current) {
        setCommandValue('');
        commandInputRef.current?.blur();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  const statusTone = loadStatus.state === 'error' ? 'error' : loadStatus.state === 'loading' ? 'loading' : loadStatus.state === 'ready' ? 'ready' : 'neutral';
  const workspaceStyle = { '--left-w': `${leftWidth}px`, '--right-w': `${rightWidth}px` } as CSSProperties;
  const activeFileName = activeModel?.name ?? 'No file selected';
  const activeFileFormat = activeModel?.model.metadata.format ?? 'STEP/STP';
  const activeStats = activeModel
    ? `${activeModel.model.metadata.meshCount.toLocaleString()} mesh${activeModel.model.metadata.meshCount === 1 ? '' : 'es'} · ${activeModel.model.metadata.vertexCount.toLocaleString()} vertices`
    : 'Drop or choose a CAD asset';

  return (
    <div className="app-shell">
      <header className="command-bar workbench-topbar" aria-label="CAD viewer toolbar">
        <div className="brand-block">
          <div className="brand-mark" aria-hidden="true"><Icon name="cube" /></div>
          <div>
            <h1>Zen CAD</h1>
            <p className="product-label">Workbench</p>
          </div>
        </div>

        <nav className="breadcrumb-bar" aria-label="Workspace path">
          <span>Projects</span>
          <Icon name="chevron-right" />
          <span>Viewer</span>
          <Icon name="chevron-right" />
          <strong title={activeFileName}>{activeFileName}</strong>
        </nav>

        <form className="command-search" role="search" aria-label="Open model or search workspace" onSubmit={handleCommandSubmit}>
          <Icon name="search" />
          <input
            ref={commandInputRef}
            value={commandValue}
            placeholder="Open URL, sample, or search loaded parts"
            aria-label="Open model URL, sample name, or search loaded parts"
            onChange={(event) => setCommandValue(event.currentTarget.value)}
          />
          <kbd>Ctrl K</kbd>
        </form>

        <div className="toolbar-band toolbar-band-load" aria-label="Load model controls">
          <input
            ref={inputRef}
            className="visually-hidden"
            id="model-file-input"
            type="file"
            accept={acceptedModelTypes}
            aria-label="Choose a STEP, STL, OBJ, glTF, or GLB model file"
            tabIndex={-1}
            onChange={(event) => {
              handleFiles(event.target.files);
              event.currentTarget.value = '';
            }}
          />
          {models.length > 0 && (
            <button type="button" className="control-button secondary-action topbar-clear" onClick={handleClearWorkspace} aria-label="Clear loaded models">
              <Icon name="reset" />
              <span>Clear</span>
            </button>
          )}
          <button type="button" className="control-button primary-action" onClick={() => inputRef.current?.click()} aria-label="Choose a STEP, STL, OBJ, glTF, or GLB model file">
            <Icon name="upload" />
            <span>Open</span>
          </button>
        </div>
      </header>

      <main className="workspace" style={workspaceStyle} onDrop={handleDrop} onDragOver={(event) => { event.preventDefault(); event.dataTransfer.dropEffect = 'copy'; }}>
        {panelState.scene ? (
          <>
            <ScenePanel
              parts={articulation?.parts ?? []}
              filterQuery={explorerQuery}
              onFilterChange={setExplorerQuery}
              recentOpens={recentOpens}
              onBrowse={() => inputRef.current?.click()}
              onPathLoad={(path, label) => void loadPath(path, label)}
              onSampleLoad={loadSample}
            />
            <Resizer side="left" />
          </>
        ) : (
          <PanelRail side="left" icon="scene" label="Scene" onExpand={() => togglePanel('scene')} />
        )}

        <section className="viewport-card" aria-label="Model viewport and drop zone">
          <div className="viewport-topline">
            <div className="viewport-file-tab" role={loadStatus.state === 'error' ? 'alert' : 'status'} aria-live="polite" data-tone={statusTone}>
              <StatusIcon state={loadStatus.state} />
              <div>
                <strong title={activeFileName}>{activeFileName}</strong>
                <span>{activeFileFormat} · {activeStats}</span>
              </div>
            </div>
            {models.length > 0 && (
              <div className="view-meta" aria-label="Current view state">
                <span>{renderModes.find((mode) => mode.id === renderMode)?.label}</span>
                <span>{cameraPresets.find((preset) => preset.id === cameraPreset)?.label}</span>
              </div>
            )}
          </div>
          <div className="canvas-wrap">
            {models.length > 0 ? (
              <ViewportCanvas articulation={articulation} animations={animations} activeModelId={activeModelId} />
            ) : (
              <div className="canvas-placeholder" aria-hidden="true" />
            )}
            {models.length === 0 && <EmptyState onBrowse={() => inputRef.current?.click()} onSampleLoad={loadSample} />}
            {models.length > 0 && (
              <>
                <ViewportToolRail />
                <CameraPresetDock />
              </>
            )}
          </div>
          <footer className="viewport-statusbar">
            <div className="status-row" role={loadStatus.state === 'error' ? 'alert' : 'status'} aria-live="polite" data-tone={statusTone}>
              <StatusIcon state={loadStatus.state} />
              <span>{loadStatus.message}</span>
            </div>
            {models.length > 0 && (
              <div className="status-metrics" aria-label="Viewport metrics">
                <span>X: 0.00</span>
                <span>Y: 0.00</span>
                <span>Z: 0.00</span>
                <span>Grid: 10 mm</span>
              </div>
            )}
          </footer>
        </section>

        {panelState.properties ? (
          <>
            <Resizer side="right" />
            <PropertiesPanel parts={articulation?.parts ?? []} animations={animations} activeModelId={activeModelId} />
          </>
        ) : (
          <PanelRail side="right" icon="properties" label="Properties" onExpand={() => togglePanel('properties')} />
        )}
      </main>
    </div>
  );
}

function Resizer({ side }: { side: 'left' | 'right' }) {
  const ref = useRef<HTMLDivElement>(null);
  const leftWidth = useViewerStore((state) => state.leftWidth);
  const rightWidth = useViewerStore((state) => state.rightWidth);
  const setLeftWidth = useViewerStore((state) => state.setLeftWidth);
  const setRightWidth = useViewerStore((state) => state.setRightWidth);
  const width = side === 'left' ? leftWidth : rightWidth;
  const setWidth = side === 'left' ? setLeftWidth : setRightWidth;

  const panelElement = () => (side === 'left' ? ref.current?.previousElementSibling : ref.current?.nextElementSibling) as HTMLElement | null;

  const handlePointerDown = (event: ReactPointerEvent<HTMLDivElement>) => {
    event.preventDefault();
    const startX = event.clientX;
    const startWidth = width;
    const panel = panelElement();
    const floor = panel ? measurePanelFloor(panel) : PANEL_FALLBACK_MIN;
    const max = panelMaxWidth();
    document.body.classList.add('resizing');

    const handleMove = (moveEvent: PointerEvent) => {
      const delta = moveEvent.clientX - startX;
      const next = side === 'left' ? startWidth + delta : startWidth - delta;
      setWidth(Math.min(max, Math.max(floor, next)));
    };
    const handleUp = () => {
      document.body.classList.remove('resizing');
      window.removeEventListener('pointermove', handleMove);
      window.removeEventListener('pointerup', handleUp);
    };
    window.addEventListener('pointermove', handleMove);
    window.addEventListener('pointerup', handleUp);
  };

  const handleKeyDown = (event: ReactKeyboardEvent<HTMLDivElement>) => {
    if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
    event.preventDefault();
    const step = event.shiftKey ? 32 : 12;
    const panel = panelElement();
    const floor = panel ? measurePanelFloor(panel) : PANEL_FALLBACK_MIN;
    const max = panelMaxWidth();
    const grow = side === 'left' ? event.key === 'ArrowRight' : event.key === 'ArrowLeft';
    const next = grow ? width + step : width - step;
    setWidth(Math.min(max, Math.max(floor, next)));
  };

  const handleDoubleClick = () => {
    const panel = panelElement();
    if (panel) setWidth(measurePanelFloor(panel));
  };

  return (
    <div
      ref={ref}
      className="resizer"
      role="separator"
      aria-orientation="vertical"
      aria-label={`Resize ${side === 'left' ? 'scene' : 'properties'} panel`}
      aria-valuenow={Math.round(width)}
      aria-valuemin={PANEL_FALLBACK_MIN}
      aria-valuemax={600}
      tabIndex={0}
      title="Drag to resize · double-click to fit"
      onPointerDown={handlePointerDown}
      onKeyDown={handleKeyDown}
      onDoubleClick={handleDoubleClick}
    />
  );
}

function ViewportToolRail() {
  const renderMode = useViewerStore((state) => state.renderMode);
  const setRenderMode = useViewerStore((state) => state.setRenderMode);
  const requestFit = useViewerStore((state) => state.requestFit);
  const requestReset = useViewerStore((state) => state.requestReset);

  return (
    <div className="viewport-tool-rail" role="toolbar" aria-label="Viewport render tools">
      {renderModes.map((mode) => (
        <button
          key={mode.id}
          type="button"
          aria-pressed={renderMode === mode.id}
          aria-label={`${mode.label} render mode: ${mode.description}`}
          title={mode.label}
          className="tool-rail-button"
          data-active={renderMode === mode.id}
          onClick={() => setRenderMode(mode.id)}
        >
          <Icon name={mode.icon} />
          <span>{mode.railLabel}</span>
        </button>
      ))}
      <span className="tool-rail-separator" aria-hidden="true" />
      <button type="button" className="tool-rail-button" onClick={requestFit} aria-label="Fit model to view" title="Fit">
        <Icon name="fit" />
        <span>Fit</span>
      </button>
      <button type="button" className="tool-rail-button" onClick={requestReset} aria-label="Reset camera to isometric view" title="Reset">
        <Icon name="reset" />
        <span>Reset</span>
      </button>
    </div>
  );
}

function CameraPresetDock() {
  const cameraPreset = useViewerStore((state) => state.cameraPreset);
  const setCameraPreset = useViewerStore((state) => state.setCameraPreset);

  return (
    <div className="camera-preset-dock" role="toolbar" aria-label="Camera presets">
      {cameraPresets.map((preset) => (
        <button
          key={preset.id}
          type="button"
          aria-pressed={cameraPreset === preset.id}
          aria-label={`${preset.label} camera preset`}
          title={preset.label}
          className="dock-button"
          data-active={cameraPreset === preset.id}
          onClick={() => setCameraPreset(preset.id)}
        >
          <Icon name={cameraIcons[preset.id]} />
          <span>{preset.label}</span>
        </button>
      ))}
    </div>
  );
}

function PanelRail({ side, icon, label, onExpand }: { side: 'left' | 'right'; icon: IconName; label: string; onExpand: () => void }) {
  return (
    <aside className={`panel-rail panel-rail-${side}`} aria-label={`${label} panel, collapsed`}>
      <button type="button" className="rail-expand" onClick={onExpand} aria-label={`Expand ${label} panel`} title={`Expand ${label}`}>
        <Icon name={icon} />
        <Icon name={side === 'left' ? 'chevron-right' : 'chevron-left'} />
      </button>
      <span className="rail-label" aria-hidden="true">{label}</span>
    </aside>
  );
}

function EmptyState({ onBrowse, onSampleLoad }: { onBrowse: () => void; onSampleLoad: (sample: (typeof sampleModels)[number]) => Promise<void> }) {
  return (
    <div className="empty-state" aria-label="Drop zone instructions">
      <div className="empty-illustration" aria-hidden="true">
        <div className="iso-cube"><Icon name="step" /></div>
        <div className="drop-orbit orbit-a" />
        <div className="drop-orbit orbit-b" />
      </div>
      <div className="drop-badge"><Icon name="step" /> STEP-ready · OpenCascade WASM</div>
      <h2>Drop a CAD model to inspect it instantly</h2>
      <p>{supportedModelHint()} Load the bundled STEP cube to verify true B-rep tessellation without external assets.</p>
      <div className="empty-actions">
        <button type="button" className="control-button primary-action" onClick={onBrowse} aria-label="Browse for a STEP, STL, OBJ, glTF, or GLB model file">
          <Icon name="upload" />
          <span>Browse files</span>
        </button>
        {sampleModels.map((sample) => (
          <button key={sample.path} type="button" className={sample.format === 'STEP' ? 'control-button accent-action' : 'control-button secondary-action'} onClick={() => void onSampleLoad(sample)} aria-label={`Load bundled sample ${sample.label}: ${sample.description}`}>
            <Icon name={sample.format === 'STEP' ? 'step' : 'cube'} />
            <span>{sample.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function ViewportCanvas({ articulation, animations, activeModelId }: { articulation: ArticulationContext | null; animations: THREE.AnimationClip[]; activeModelId: string | null }) {
  const sceneGroupRef = useRef<THREE.Group>(null);
  const models = useViewerStore((state) => state.models);
  const renderMode = useViewerStore((state) => state.renderMode);
  const showOverlaps = useViewerStore((state) => state.showOverlaps);
  const visibleModels = models.filter((entry) => entry.visible);
  const activeModel = models.find((entry) => entry.id === activeModelId) ?? null;
  const focusObject = activeModel?.visible ? activeModel.model.group : null;
  // AO radius lives in world units, but models are never scaled (real mm/cm), so
  // size the ambient-occlusion reach to the largest visible model's span.
  const sceneSpan = visibleModels.reduce((max, entry) => Math.max(max, modelSpan(entry.model.metadata.size)), 1);

  if (shouldUseAutomatedCanvas()) return <AutomatedCanvas />;

  return (
    <Canvas orthographic frameloop="demand" camera={{ position: [4, 4, 4], zoom: 72, near: 0.01, far: 2000 }} gl={{ antialias: true, powerPreference: 'low-power' }} shadows dpr={[1, 1.5]}>
      <color attach="background" args={["#fafafa"]} />
      <ambientLight intensity={0.82} />
      <directionalLight position={[6, 8, 6]} intensity={1.45} castShadow />
      <directionalLight position={[-5, -2, -4]} intensity={0.5} />
      <Suspense fallback={null}>
        <group ref={sceneGroupRef}>
          <ViewerScene models={models} renderMode={renderMode} />
        </group>
      </Suspense>
      {articulation && activeModelId && <Articulator articulation={articulation} modelId={activeModelId} animations={animations} />}
      {showOverlaps && articulation && <OverlapView articulation={articulation} modelId={activeModelId ?? ''} />}
      {visibleModels.length > 0 && <PostFX span={sceneSpan} />}
      <CameraRig fitObject={sceneGroupRef.current} focusObject={focusObject} visibleModelCount={visibleModels.length} activeModelId={activeModelId} />
      <GizmoHelper alignment="top-right" margin={[64, 72]}>
        <GizmoViewport axisColors={["#ef4444", "#22a06b", "#f59e0b"]} labelColor="#202124" />
      </GizmoHelper>
    </Canvas>
  );
}

// Screen-space ambient occlusion (N8AO). Darkens crevices, holes and contact
// seams so part boundaries read clearly on flat-shaded CAD geometry — pairs with
// the shadow map rather than replacing it. multisampling keeps edges anti-aliased
// once the composer takes over the main render pass.
function PostFX({ span }: { span: number }) {
  const aoRadius = Math.max(span * 0.055, 0.05);
  return (
    <EffectComposer multisampling={8} enableNormalPass={false}>
      <N8AO
        aoRadius={aoRadius}
        distanceFalloff={1}
        intensity={1.35}
        quality="medium"
        halfRes={false}
        color="#9aa0a6"
      />
    </EffectComposer>
  );
}

function Articulator({ articulation, modelId, animations }: { articulation: ArticulationContext; modelId: string; animations: THREE.AnimationClip[] }) {
  const partTransforms = useViewerStore((state) => state.partTransforms);
  const autoSpin = useViewerStore((state) => state.autoSpin);
  const explode = useViewerStore((state) => state.explode[modelId] ?? 0);
  const playing = useViewerStore((state) => state.animationPlaying);
  const clipIndex = useViewerStore((state) => state.animationClipIndex);
  const speed = useViewerStore((state) => state.animationSpeed);
  const invalidate = useThree((state) => state.invalidate);
  const mixerRef = useRef<THREE.AnimationMixer | null>(null);

  const partByUuid = useMemo(() => {
    const map = new Map<string, THREE.Object3D>();
    articulation.parts.forEach((part) => map.set(part.uuid, part.node));
    return map;
  }, [articulation]);

  const temps = useMemo(() => ({
    euler: new THREE.Euler(),
    quat: new THREE.Quaternion(),
    spinQuat: new THREE.Quaternion(),
    spinAxis: new THREE.Vector3(),
    offset: new THREE.Vector3(),
  }), []);

  useEffect(() => {
    if (!animations.length) {
      mixerRef.current = null;
      return undefined;
    }
    const mixer = new THREE.AnimationMixer(articulation.group);
    mixerRef.current = mixer;
    return () => {
      mixer.stopAllAction();
      mixerRef.current = null;
    };
  }, [animations, articulation.group]);

  useEffect(() => {
    const mixer = mixerRef.current;
    if (!mixer) return;
    mixer.stopAllAction();
    if (playing && animations.length) {
      const clip = animations[clipIndex] ?? animations[0];
      if (clip) mixer.clipAction(clip).reset().play();
    }
    invalidate();
  }, [playing, clipIndex, animations, invalidate]);

  // Static pose (applies when not animating); auto-spin is layered in useFrame.
  useEffect(() => {
    if (playing) return;
    articulation.parts.forEach((part) => {
      const base = articulation.bases.get(part.uuid);
      if (!base) return;
      const transform = partTransforms[part.uuid];
      const rotation = transform?.rotation ?? [0, 0, 0];
      const position = transform?.position ?? [0, 0, 0];
      temps.euler.set(THREE.MathUtils.degToRad(rotation[0]), THREE.MathUtils.degToRad(rotation[1]), THREE.MathUtils.degToRad(rotation[2]));
      temps.quat.setFromEuler(temps.euler);
      part.node.quaternion.copy(base.quaternion).multiply(temps.quat);
      temps.offset.set(position[0], position[1], position[2]).addScaledVector(base.explodeVec, explode);
      part.node.position.copy(base.position).add(temps.offset);
    });
    invalidate();
  }, [partTransforms, explode, playing, autoSpin, articulation, temps, invalidate]);

  useFrame((state, delta) => {
    let active = false;
    const mixer = mixerRef.current;
    if (mixer && playing) {
      mixer.update(delta * speed);
      active = true;
    }
    if (!playing) {
      const uuids = Object.keys(autoSpin);
      if (uuids.length) {
        const elapsed = state.clock.getElapsedTime();
        uuids.forEach((uuid) => {
          const node = partByUuid.get(uuid);
          const base = articulation.bases.get(uuid);
          if (!node || !base) return;
          const config = autoSpin[uuid];
          const manual = partTransforms[uuid];
          temps.euler.set(
            THREE.MathUtils.degToRad(manual?.rotation[0] ?? 0),
            THREE.MathUtils.degToRad(manual?.rotation[1] ?? 0),
            THREE.MathUtils.degToRad(manual?.rotation[2] ?? 0),
          );
          temps.quat.setFromEuler(temps.euler);
          temps.spinAxis.set(config.axis === 0 ? 1 : 0, config.axis === 1 ? 1 : 0, config.axis === 2 ? 1 : 0);
          temps.spinQuat.setFromAxisAngle(temps.spinAxis, elapsed * config.speed);
          node.quaternion.copy(base.quaternion).multiply(temps.quat).multiply(temps.spinQuat);
        });
        active = true;
      }
    }
    if (active) invalidate();
  });

  return null;
}

function OverlapView({ articulation, modelId }: { articulation: ArticulationContext; modelId: string }) {
  const partTransforms = useViewerStore((state) => state.partTransforms);
  const explodeFactor = useViewerStore((state) => state.explode[modelId] ?? 0);
  const hiddenParts = useViewerStore((state) => state.hiddenParts);
  const playing = useViewerStore((state) => state.animationPlaying);
  const spinning = useViewerStore((state) => Object.keys(state.autoSpin).length > 0);
  const setOverlapCount = useViewerStore((state) => state.setOverlapCount);
  const setOverlapFrozen = useViewerStore((state) => state.setOverlapFrozen);
  const invalidate = useThree((state) => state.invalidate);
  const [geometries, setGeometries] = useState<THREE.BufferGeometry[]>([]);
  const live = useRef({ at: 0, interval: 150, lastMs: 0 });

  const recompute = useCallback(() => {
    const started = performance.now();
    // Hidden parts don't interfere — paint and count only what's on screen.
    const visibleParts = articulation.parts.filter((part) => !hiddenParts[part.uuid]);
    const { geometries: next, pairs } = computeOverlapVolumes(visibleParts);
    live.current.lastMs = performance.now() - started;
    setOverlapCount(pairs);
    setGeometries(next);
    invalidate();
  }, [articulation, hiddenParts, setOverlapCount, invalidate]);

  // At rest: debounced precise recompute (also refreshes once motion stops).
  useEffect(() => {
    if (playing || spinning) return undefined;
    const handle = setTimeout(recompute, 140);
    return () => clearTimeout(handle);
  }, [partTransforms, explodeFactor, hiddenParts, playing, spinning, recompute]);

  // During motion: live but throttled, and only while a single recompute stays
  // cheap enough not to jank the rotation; heavy models freeze until they rest.
  useFrame(() => {
    if (!(playing || spinning)) return;
    if (live.current.lastMs > LIVE_OVERLAP_BUDGET_MS) {
      setOverlapFrozen(true);
      return;
    }
    const now = performance.now();
    if (now - live.current.at < live.current.interval) return;
    live.current.at = now;
    setOverlapFrozen(false);
    recompute();
    live.current.interval = Math.max(150, live.current.lastMs * 5);
  });

  // Re-evaluate heaviness on the next motion once this one ends.
  useEffect(() => {
    if (!playing && !spinning) {
      live.current.at = 0;
      setOverlapFrozen(false);
    }
  }, [playing, spinning, setOverlapFrozen]);

  // Dispose the previous GPU geometries when replaced or on unmount.
  useEffect(() => () => { geometries.forEach((geom) => geom.dispose()); }, [geometries]);

  // Clear the frozen flag when overlaps are switched off (view unmounts).
  useEffect(() => () => setOverlapFrozen(false), [setOverlapFrozen]);

  if (geometries.length === 0) return null;
  return (
    <group renderOrder={6}>
      {geometries.map((geom, index) => (
        <mesh key={index} geometry={geom} renderOrder={6}>
          <meshBasicMaterial color="#ff4d57" transparent opacity={0.55} side={THREE.DoubleSide} depthWrite={false} />
        </mesh>
      ))}
    </group>
  );
}

function AutomatedCanvas() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const renderMode = useViewerStore((state) => state.renderMode);
  const cameraPreset = useViewerStore((state) => state.cameraPreset);
  const modelCount = useViewerStore((state) => state.models.length);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const draw = () => {
      const rect = canvas.getBoundingClientRect();
      const width = Math.max(320, Math.floor(rect.width));
      const height = Math.max(240, Math.floor(rect.height));
      canvas.width = width;
      canvas.height = height;
      const ctx = canvas.getContext('2d');
      if (!ctx) return;
      ctx.fillStyle = '#fafafa';
      ctx.fillRect(0, 0, width, height);
      ctx.strokeStyle = 'rgba(17, 17, 19, 0.07)';
      ctx.lineWidth = 1;
      for (let x = 0; x < width; x += 34) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, height);
        ctx.stroke();
      }
      for (let y = 0; y < height; y += 34) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(width, y);
        ctx.stroke();
      }

      const modeColors: Record<RenderMode, string> = {
        shaded: '#6f7d8f',
        wireframe: '#202124',
        overlay: '#3f4248',
        xray: '#8d99a8',
        normals: '#22a06b',
        points: '#ef7730',
      };
      const cameraOffsets: Record<CameraPreset, [number, number]> = {
        top: [0, -42],
        bottom: [0, 42],
        front: [0, 0],
        back: [42, 0],
        left: [-42, 0],
        right: [42, 0],
        isometric: [24, -24],
      };
      const [offsetX, offsetY] = cameraOffsets[cameraPreset];
      const cx = width / 2 + offsetX;
      const cy = height / 2 + offsetY;
      const color = modeColors[renderMode];

      ctx.save();
      ctx.translate(cx, cy);
      ctx.rotate(cameraPreset === 'isometric' ? -Math.PI / 6 : 0);
      ctx.globalAlpha = renderMode === 'xray' ? 0.38 : 0.88;
      ctx.fillStyle = color;
      ctx.strokeStyle = color;
      ctx.lineWidth = renderMode === 'wireframe' ? 3 : 2;
      const size = Math.min(width, height) * 0.19;
      if (renderMode === 'points') {
        for (let i = 0; i < 36; i += 1) {
          const px = Math.sin(i * 1.7) * 0.9 * size;
          const py = Math.cos(i * 1.1) * 0.65 * size;
          ctx.beginPath();
          ctx.arc(px, py, 4, 0, Math.PI * 2);
          ctx.fill();
        }
      } else {
        ctx.beginPath();
        ctx.moveTo(-size, -size * 0.42);
        ctx.lineTo(0, -size);
        ctx.lineTo(size, -size * 0.42);
        ctx.lineTo(size, size * 0.55);
        ctx.lineTo(0, size);
        ctx.lineTo(-size, size * 0.55);
        ctx.closePath();
        if (renderMode !== 'wireframe') ctx.fill();
        ctx.stroke();
        if (renderMode === 'wireframe' || renderMode === 'overlay' || renderMode === 'xray') {
          ctx.beginPath();
          ctx.moveTo(-size, -size * 0.42);
          ctx.lineTo(0, 0);
          ctx.lineTo(size, -size * 0.42);
          ctx.moveTo(0, 0);
          ctx.lineTo(0, size);
          ctx.strokeStyle = '#eef2f6';
          ctx.stroke();
        }
        if (renderMode === 'normals') {
          ctx.strokeStyle = '#5ee0a0';
          for (let i = -2; i <= 2; i += 1) {
            ctx.beginPath();
            ctx.moveTo(i * size * 0.32, size * 0.2);
            ctx.lineTo(i * size * 0.32, -size * 0.65);
            ctx.stroke();
          }
        }
      }
      ctx.restore();

      ctx.fillStyle = '#a5f3ec';
      ctx.font = '700 18px "Space Grotesk", system-ui, sans-serif';
      ctx.fillText(`${renderMode} · ${cameraPreset} · ${modelCount} model`, 24, 36);
    };
    draw();
    const observer = new ResizeObserver(draw);
    observer.observe(canvas);
    return () => observer.disconnect();
  }, [cameraPreset, modelCount, renderMode]);

  return <canvas ref={canvasRef} className="automation-canvas" aria-hidden="true" />;
}

function CameraRig({
  fitObject,
  focusObject,
  visibleModelCount,
  activeModelId,
}: {
  fitObject: THREE.Object3D | null;
  focusObject: THREE.Object3D | null;
  visibleModelCount: number;
  activeModelId: string | null;
}) {
  const controlsRef = useRef<any>(null);
  const { camera, size } = useThree();
  const cameraPreset = useViewerStore((state) => state.cameraPreset);
  const viewRevision = useViewerStore((state) => state.viewRevision);
  const fitRevision = useViewerStore((state) => state.fitRevision);
  const resetRevision = useViewerStore((state) => state.resetRevision);

  useEffect(() => {
    if ((camera as THREE.OrthographicCamera).isOrthographicCamera) {
      fitOrthographicCamera(camera as THREE.OrthographicCamera, fitObject, size.width / Math.max(size.height, 1), focusObject, controlsRef.current);
    }
  }, [activeModelId, camera, fitObject, focusObject, size.height, size.width, visibleModelCount]);

  useEffect(() => {
    if ((camera as THREE.OrthographicCamera).isOrthographicCamera) {
      applyCameraPreset(camera as THREE.OrthographicCamera, controlsRef.current, fitObject, cameraPreset, size.width / Math.max(size.height, 1), focusObject);
    }
  }, [activeModelId, camera, cameraPreset, fitObject, focusObject, resetRevision, size.height, size.width, viewRevision, visibleModelCount]);

  useEffect(() => {
    if ((camera as THREE.OrthographicCamera).isOrthographicCamera) {
      fitOrthographicCamera(camera as THREE.OrthographicCamera, fitObject, size.width / Math.max(size.height, 1), focusObject, controlsRef.current);
    }
  }, [activeModelId, camera, fitObject, fitRevision, focusObject, size.height, size.width, visibleModelCount]);

  return <OrbitControls ref={controlsRef} makeDefault enableDamping dampingFactor={0.08} enablePan enableZoom enableRotate />;
}

function ScenePanel({
  parts,
  filterQuery,
  onFilterChange,
  recentOpens,
  onBrowse,
  onPathLoad,
  onSampleLoad,
}: {
  parts: PartNode[];
  filterQuery: string;
  onFilterChange: (query: string) => void;
  recentOpens: RecentOpen[];
  onBrowse: () => void;
  onPathLoad: (path: string, label?: string) => void;
  onSampleLoad: (sample: (typeof sampleModels)[number]) => Promise<void>;
}) {
  const models = useViewerStore((state) => state.models);
  const activeModelId = useViewerStore((state) => state.activeModelId);
  const activePartUuid = useViewerStore((state) => state.activePartUuid);
  const toggleModelVisibility = useViewerStore((state) => state.toggleModelVisibility);
  const isolateModel = useViewerStore((state) => state.isolateModel);
  const removeModel = useViewerStore((state) => state.removeModel);
  const setActiveModel = useViewerStore((state) => state.setActiveModel);
  const setActivePart = useViewerStore((state) => state.setActivePart);
  const hiddenParts = useViewerStore((state) => state.hiddenParts);
  const togglePartVisibility = useViewerStore((state) => state.togglePartVisibility);
  const togglePanel = useViewerStore((state) => state.togglePanel);
  const normalizedQuery = filterQuery.trim().toLowerCase();
  const modelMatchesQuery = useCallback((entry: LoadedModelEntry) => (
    entry.name.toLowerCase().includes(normalizedQuery) ||
    entry.model.metadata.format.toLowerCase().includes(normalizedQuery)
  ), [normalizedQuery]);
  const filteredModels = normalizedQuery
    ? models.filter((entry) => modelMatchesQuery(entry) || (entry.id === activeModelId && parts.some((part) => part.name.toLowerCase().includes(normalizedQuery))))
    : models;
  const matchingParts = normalizedQuery
    ? parts.filter((part) => part.name.toLowerCase().includes(normalizedQuery))
    : parts;

  return (
    <aside id="scene-panel" className="panel scene-panel" aria-label="Scene tree">
      <PanelHeader icon="scene" eyebrow="Explorer" title="Model tree" side="left" onCollapse={() => togglePanel('scene')} />
      <label className="file-filter">
        <Icon name="search" />
        <span className="visually-hidden">Filter models and parts</span>
        <input value={filterQuery} placeholder="Filter files and parts" onChange={(event) => onFilterChange(event.currentTarget.value)} />
      </label>
      {models.length > 0 ? (
        <div className="model-list" role="list" aria-label="Loaded models">
          <div className="tree-folder-row" aria-hidden="true">
            <Icon name="folder" />
            <span>Zen CAD Review</span>
          </div>
          {filteredModels.length === 0 && (
            <div className="panel-empty compact">
              <Icon name="search" />
              <p>No matching files or parts.</p>
            </div>
          )}
          {filteredModels.map((entry) => {
            const isActive = activeModelId === entry.id;
            const others = models.filter((other) => other.id !== entry.id);
            const isIsolated = entry.visible && others.length > 0 && others.every((other) => !other.visible);
            const modelMatches = normalizedQuery ? modelMatchesQuery(entry) : true;
            const visibleParts = normalizedQuery && !modelMatches ? matchingParts : parts;
            return (
              <div key={entry.id} className="model-card" role="listitem" data-active={isActive} data-visible={entry.visible}>
                <div className="model-card-head">
                  <button type="button" className="model-select-button" aria-pressed={isActive} title={entry.name} onClick={() => setActiveModel(entry.id)}>
                    <Icon name="cube" />
                    <span className="model-name">{entry.name}</span>
                  </button>
                  <button
                    type="button"
                    className="visibility-toggle"
                    aria-pressed={entry.visible}
                    aria-label={`${entry.visible ? 'Hide' : 'Show'} ${entry.name}`}
                    title={entry.visible ? 'Hide' : 'Show'}
                    onClick={() => toggleModelVisibility(entry.id)}
                  >
                    <Icon name={entry.visible ? 'eye' : 'eye-off'} />
                  </button>
                </div>
                <p className="model-meta">{entry.model.metadata.format} · {entry.model.metadata.meshCount.toLocaleString()} mesh{entry.model.metadata.meshCount === 1 ? '' : 'es'} · {entry.model.metadata.vertexCount.toLocaleString()} verts</p>
                <div className="model-actions" role="group" aria-label={`${entry.name} model actions`}>
                  <button type="button" className="model-action" aria-pressed={isIsolated} title={isIsolated ? 'Show all models' : 'Show only this model'} onClick={() => isolateModel(entry.id)}>{isIsolated ? 'Show all' : 'Isolate'}</button>
                  <button type="button" className="model-action danger" onClick={() => removeModel(entry.id)}>Remove</button>
                </div>
                {isActive && visibleParts.length > 0 && (
                  <ul className="part-tree" role="tree" aria-label={`${entry.name} parts`}>
                    {visibleParts.map((part) => {
                      const partHidden = !!hiddenParts[part.uuid];
                      return (
                        <li key={part.uuid} role="treeitem" aria-selected={activePartUuid === part.uuid}>
                          <div className="part-row" data-active={activePartUuid === part.uuid} data-hidden={partHidden}>
                            <button
                              type="button"
                              className="part-item"
                              data-active={activePartUuid === part.uuid}
                              style={{ paddingLeft: `${0.1 + part.depth * 0.8}rem` }}
                              title={part.name}
                              onClick={() => setActivePart(activePartUuid === part.uuid ? null : part.uuid)}
                            >
                              <span className="mesh-dot" />
                              <span className="mesh-name">{part.name}</span>
                            </button>
                            <button
                              type="button"
                              className="part-visibility"
                              aria-pressed={!partHidden}
                              aria-label={`${partHidden ? 'Show' : 'Hide'} ${part.name}`}
                              title={partHidden ? 'Show part' : 'Hide part'}
                              onClick={() => togglePartVisibility(part.uuid)}
                            >
                              <Icon name={partHidden ? 'eye-off' : 'eye'} />
                            </button>
                          </div>
                        </li>
                      );
                    })}
                  </ul>
                )}
              </div>
            );
          })}
        </div>
      ) : (
        <QuickOpenPanel
          filterQuery={filterQuery}
          recentOpens={recentOpens}
          onBrowse={onBrowse}
          onPathLoad={onPathLoad}
          onSampleLoad={onSampleLoad}
        />
      )}
    </aside>
  );
}

function QuickOpenPanel({
  filterQuery,
  recentOpens,
  onBrowse,
  onPathLoad,
  onSampleLoad,
}: {
  filterQuery: string;
  recentOpens: RecentOpen[];
  onBrowse: () => void;
  onPathLoad: (path: string, label?: string) => void;
  onSampleLoad: (sample: (typeof sampleModels)[number]) => Promise<void>;
}) {
  const normalizedQuery = filterQuery.trim().toLowerCase();
  const visibleSamples = normalizedQuery
    ? sampleModels.filter((sample) => sampleMatchesCommand(sample, normalizedQuery))
    : sampleModels;
  const visibleRecentOpens = normalizedQuery
    ? recentOpens.filter((item) => (
      item.label.toLowerCase().includes(normalizedQuery) ||
      item.path.toLowerCase().includes(normalizedQuery) ||
      item.format.toLowerCase().includes(normalizedQuery)
    ))
    : recentOpens;
  const hasResults = visibleSamples.length > 0 || visibleRecentOpens.length > 0;

  return (
    <div className="quick-open-panel" aria-label="Quick open models">
      <div className="quick-open-hero">
        <Icon name="folder" />
        <div>
          <strong>Quick open</strong>
          <span>Samples, recent paths, or a local file.</span>
        </div>
      </div>

      <button type="button" className="quick-open-primary" onClick={onBrowse}>
        <Icon name="upload" />
        <span>Choose CAD file</span>
      </button>

      {visibleSamples.length > 0 && (
        <section className="quick-section" aria-label="Bundled samples">
          <div className="quick-section-title">
            <span>Samples</span>
            <small>Bundled</small>
          </div>
          <div className="quick-file-list">
            {visibleSamples.map((sample) => (
              <button key={sample.path} type="button" className="quick-file-button" onClick={() => void onSampleLoad(sample)}>
                <Icon name={sample.format === 'STEP' ? 'step' : 'cube'} />
                <span>{sample.label}</span>
                <small>{sample.format}</small>
              </button>
            ))}
          </div>
        </section>
      )}

      {visibleRecentOpens.length > 0 && (
        <section className="quick-section" aria-label="Recent paths">
          <div className="quick-section-title">
            <span>Recent</span>
            <small>{visibleRecentOpens.length}</small>
          </div>
          <div className="quick-file-list">
            {visibleRecentOpens.map((item) => (
              <button key={item.path} type="button" className="quick-file-button" title={item.path} onClick={() => onPathLoad(item.path, item.label)}>
                <Icon name={item.format === 'STEP' || item.format === 'STEP/STP' ? 'step' : 'cube'} />
                <span>{item.label}</span>
                <small>{item.format}</small>
              </button>
            ))}
          </div>
        </section>
      )}

      {!hasResults && (
        <div className="panel-empty compact">
          <Icon name="search" />
          <p>No sample or recent path matches that filter.</p>
        </div>
      )}
    </div>
  );
}

type InspectorTab = 'properties' | 'parameters' | 'review';

const inspectorTabs: Array<{ id: InspectorTab; label: string; ariaLabel: string }> = [
  { id: 'properties', label: 'Props', ariaLabel: 'Properties' },
  { id: 'parameters', label: 'Params', ariaLabel: 'Parameters' },
  { id: 'review', label: 'Review', ariaLabel: 'Review' },
];

function PropertiesPanel({ parts, animations, activeModelId }: { parts: PartNode[]; animations: THREE.AnimationClip[]; activeModelId: string | null }) {
  const [tab, setTab] = useState<InspectorTab>('properties');
  const models = useViewerStore((state) => state.models);
  const renderMode = useViewerStore((state) => state.renderMode);
  const cameraPreset = useViewerStore((state) => state.cameraPreset);
  const togglePanel = useViewerStore((state) => state.togglePanel);
  const activeEntry = models.find((entry) => entry.id === activeModelId) ?? models[models.length - 1] ?? null;
  const isActive = !!activeEntry && activeEntry.id === activeModelId;

  return (
    <aside id="properties-panel" className="panel properties-panel" aria-label="Model properties">
      <PanelHeader icon="properties" eyebrow="Inspector" title="Review sheet" side="right" onCollapse={() => togglePanel('properties')} />
      {activeEntry ? (
        <div className="inspector-body">
          <div className="inspector-tabs" role="tablist" aria-label="Inspector sections">
            {inspectorTabs.map((item) => (
              <button
                key={item.id}
                type="button"
                role="tab"
                aria-selected={tab === item.id}
                aria-label={item.ariaLabel}
                title={item.ariaLabel}
                className="inspector-tab"
                onClick={() => setTab(item.id)}
              >
                {item.label}
              </button>
            ))}
          </div>

          {tab === 'properties' && (
            <dl className="property-grid">
              <PropertyRow label="Name" value={activeEntry.name} />
              <PropertyRow label="Format" value={activeEntry.model.metadata.format} />
              <PropertyRow label="Source" value={activeEntry.model.metadata.source} />
              <PropertyRow label="Meshes" value={activeEntry.model.metadata.meshCount.toLocaleString()} />
              <PropertyRow label="Vertices" value={activeEntry.model.metadata.vertexCount.toLocaleString()} />
              <PropertyRow label="Size" value={activeEntry.model.metadata.size.map((value) => value.toFixed(2)).join(' × ')} />
              <PropertyRow label="Render" value={renderMode} />
              <PropertyRow label="Camera" value={cameraPreset} />
            </dl>
          )}

          {tab === 'parameters' && isActive && activeModelId && (
            <ArticulationControls
              modelId={activeModelId}
              parts={parts}
              animations={animations}
              span={modelSpan(activeEntry.model.metadata.size)}
            />
          )}

          {tab === 'parameters' && (!isActive || !activeModelId) && (
            <div className="panel-empty compact">
              <Icon name="joint" />
              <p>Select an active model to edit part transforms and motion.</p>
            </div>
          )}

          {tab === 'review' && (
            <ReviewChecklist activeEntry={activeEntry} parts={parts} animations={animations} renderMode={renderMode} cameraPreset={cameraPreset} />
          )}
        </div>
      ) : (
        <div className="panel-empty">
          <Icon name="properties" />
          <p>Load a model to inspect format, dimensions, mesh count, and active viewport settings.</p>
        </div>
      )}
    </aside>
  );
}

function ReviewChecklist({
  activeEntry,
  parts,
  animations,
  renderMode,
  cameraPreset,
}: {
  activeEntry: LoadedModelEntry | null;
  parts: PartNode[];
  animations: THREE.AnimationClip[];
  renderMode: RenderMode;
  cameraPreset: CameraPreset;
}) {
  const hiddenParts = useViewerStore((state) => state.hiddenParts);
  const showOverlaps = useViewerStore((state) => state.showOverlaps);
  const overlapCount = useViewerStore((state) => state.overlapCount);
  const hasHiddenParts = parts.some((part) => hiddenParts[part.uuid]);
  const size = activeEntry?.model.metadata.size ?? [0, 0, 0];
  const hasVolume = size.some((value) => value > 0);
  const checks = [
    { label: 'Model loaded', status: !!activeEntry, detail: activeEntry?.name ?? 'No file' },
    { label: 'Bounding box available', status: hasVolume, detail: size.map((value) => value.toFixed(2)).join(' x ') },
    { label: 'Renderable meshes', status: (activeEntry?.model.metadata.meshCount ?? 0) > 0, detail: `${activeEntry?.model.metadata.meshCount ?? 0} mesh records` },
    { label: 'Viewport state', status: true, detail: `${renderMode} / ${cameraPreset}` },
    { label: 'Part visibility', status: !hasHiddenParts, detail: hasHiddenParts ? 'Some parts hidden' : `${parts.length} visible part records` },
    { label: 'Overlap review', status: !showOverlaps || overlapCount === 0, detail: showOverlaps ? `${overlapCount} overlap pair${overlapCount === 1 ? '' : 's'}` : 'Not enabled' },
    { label: 'Animation clips', status: true, detail: animations.length > 0 ? `${animations.length} clip${animations.length === 1 ? '' : 's'}` : 'No animation tracks' },
  ];

  return (
    <section className="review-checklist" aria-label="Review checks">
      <div className="review-summary">
        <Icon name={checks.every((check) => check.status) ? 'check' : 'alert'} />
        <div>
          <strong>{checks.every((check) => check.status) ? 'No visible review blockers' : 'Review attention needed'}</strong>
          <span>Visual evidence remains secondary to geometry inspection reports.</span>
        </div>
      </div>
      <ul>
        {checks.map((check) => (
          <li key={check.label} data-passed={check.status}>
            <Icon name={check.status ? 'check' : 'alert'} />
            <div>
              <strong>{check.label}</strong>
              <span>{check.detail}</span>
            </div>
          </li>
        ))}
      </ul>
    </section>
  );
}

function ArticulationControls({ modelId, parts, animations, span }: { modelId: string; parts: PartNode[]; animations: THREE.AnimationClip[]; span: number }) {
  const activePartUuid = useViewerStore((state) => state.activePartUuid);
  const partTransforms = useViewerStore((state) => state.partTransforms);
  const partColors = useViewerStore((state) => state.partColors);
  const hiddenParts = useViewerStore((state) => state.hiddenParts);
  const autoSpin = useViewerStore((state) => state.autoSpin);
  const explode = useViewerStore((state) => state.explode[modelId] ?? 0);
  const showOverlaps = useViewerStore((state) => state.showOverlaps);
  const overlapCount = useViewerStore((state) => state.overlapCount);
  const overlapFrozen = useViewerStore((state) => state.overlapFrozen);
  const playing = useViewerStore((state) => state.animationPlaying);
  const clipIndex = useViewerStore((state) => state.animationClipIndex);
  const speed = useViewerStore((state) => state.animationSpeed);
  const setPartRotation = useViewerStore((state) => state.setPartRotation);
  const setPartPosition = useViewerStore((state) => state.setPartPosition);
  const resetPart = useViewerStore((state) => state.resetPart);
  const setPartColor = useViewerStore((state) => state.setPartColor);
  const clearPartColor = useViewerStore((state) => state.clearPartColor);
  const togglePartVisibility = useViewerStore((state) => state.togglePartVisibility);
  const isolatePart = useViewerStore((state) => state.isolatePart);
  const showAllParts = useViewerStore((state) => state.showAllParts);
  const toggleAutoSpin = useViewerStore((state) => state.toggleAutoSpin);
  const setAutoSpinAxis = useViewerStore((state) => state.setAutoSpinAxis);
  const setAutoSpinSpeed = useViewerStore((state) => state.setAutoSpinSpeed);
  const setExplode = useViewerStore((state) => state.setExplode);
  const setShowOverlaps = useViewerStore((state) => state.setShowOverlaps);
  const clearArticulation = useViewerStore((state) => state.clearArticulation);
  const setAnimationPlaying = useViewerStore((state) => state.setAnimationPlaying);
  const setAnimationClipIndex = useViewerStore((state) => state.setAnimationClipIndex);
  const setAnimationSpeed = useViewerStore((state) => state.setAnimationSpeed);

  const activePart = parts.find((part) => part.uuid === activePartUuid) ?? null;
  const transform = (activePart && partTransforms[activePart.uuid]) || { rotation: [0, 0, 0], position: [0, 0, 0] };
  const partColor = (activePart && partColors[activePart.uuid]) || '#8aa0bd';
  const hasColor = !!(activePart && partColors[activePart.uuid]);
  const spin = activePart ? autoSpin[activePart.uuid] : undefined;
  const topLevelCount = parts.filter((part) => part.topLevel).length;
  const posRange = Math.max(span, 0.01);
  const posStep = Math.max(posRange / 200, 0.001);
  const modelUuids = parts.map((part) => part.uuid);
  const anyHidden = parts.some((part) => hiddenParts[part.uuid]);
  const activeHidden = !!(activePart && hiddenParts[activePart.uuid]);
  const isolationKeep = activePart ? isolationScope(activePart, parts) : [];
  const activeIsolated = !!activePart && anyHidden && modelUuids.every((u) => Boolean(hiddenParts[u]) === !isolationKeep.includes(u));
  const hasArticulation = Object.keys(partTransforms).length > 0 || Object.keys(partColors).length > 0 || Object.keys(autoSpin).length > 0 || explode > 0 || anyHidden;

  if (parts.length === 0 && animations.length === 0) {
    return (
      <section className="control-section" aria-label="Articulation">
        <h3 className="control-heading"><Icon name="joint" /> Articulation</h3>
        <p className="control-hint">This model exposes no separable parts to pose.</p>
      </section>
    );
  }

  return (
    <section className="control-section" aria-label="Articulation">
      <div className="control-heading-row">
        <h3 className="control-heading"><Icon name="joint" /> Articulation</h3>
        <div className="model-actions" role="group" aria-label="Articulation actions">
          {anyHidden && (
            <button type="button" className="model-action" onClick={() => showAllParts(modelUuids)}>Show all parts</button>
          )}
          {hasArticulation && (
            <button type="button" className="model-action" onClick={() => clearArticulation(modelId, parts.map((part) => part.uuid))}>Reset all</button>
          )}
        </div>
      </div>

      {animations.length > 0 && (
        <div className="control-block">
          <div className="control-block-head">
            <span className="control-label">Animation</span>
            <button
              type="button"
              className="control-button secondary-action play-button"
              aria-pressed={playing}
              onClick={() => setAnimationPlaying(!playing)}
            >
              <Icon name={playing ? 'pause' : 'play'} />
              <span>{playing ? 'Pause' : 'Play'}</span>
            </button>
          </div>
          {animations.length > 1 && (
            <label className="select-field">
              <span className="visually-hidden">Animation clip</span>
              <select value={clipIndex} onChange={(event) => setAnimationClipIndex(Number(event.currentTarget.value))}>
                {animations.map((clip, index) => <option key={clip.uuid} value={index}>{clip.name || `Clip ${index + 1}`}</option>)}
              </select>
            </label>
          )}
          <RangeField label="Speed" value={speed} min={0.1} max={3} step={0.1} unit="×" onChange={setAnimationSpeed} />
        </div>
      )}

      {topLevelCount > 1 && (
        <div className="control-block">
          <RangeField label="Explode" value={Math.round(explode * 100)} min={0} max={100} step={1} unit="%" onChange={(value) => setExplode(modelId, value / 100)} />
          <div className="control-block-head">
            <span className="control-label">Overlap check</span>
            <button type="button" className="control-button secondary-action play-button" aria-pressed={showOverlaps} onClick={() => setShowOverlaps(!showOverlaps)}>
              <Icon name="overlap" />
              <span>{showOverlaps ? `${overlapCount} found` : 'Off'}</span>
            </button>
          </div>
          {showOverlaps && <p className="control-hint">{overlapCount > 0 ? `${overlapCount} interfering pair${overlapCount === 1 ? '' : 's'} — overlapping volume painted red.` : 'No parts interfere.'}</p>}
          {showOverlaps && overlapFrozen && (
            <p className="control-note"><Icon name="pause" /> Paused while moving — too heavy to update live; refreshes when motion stops.</p>
          )}
        </div>
      )}

      <div className="control-block">
        {activePart ? (
          <>
            <div className="control-block-head">
              <span className="control-label" title={activePart.name}>Part · {activePart.name}</span>
              <button type="button" className="model-action" onClick={() => resetPart(activePart.uuid)}>Reset</button>
            </div>

            <div className="color-row">
              <span className="control-sublabel color-label">Color</span>
              <input type="color" className="color-input" value={partColor} aria-label="Part color" onChange={(event) => setPartColor(activePart.uuid, event.currentTarget.value)} />
              {hasColor && <button type="button" className="model-action" onClick={() => clearPartColor(activePart.uuid)}>Clear</button>}
            </div>

            <div className="control-block-head">
              <span className="control-sublabel color-label">Visibility</span>
              <div className="model-actions" role="group" aria-label="Part visibility">
                <button type="button" className="model-action" aria-pressed={activeHidden} onClick={() => togglePartVisibility(activePart.uuid)}>{activeHidden ? 'Show' : 'Hide'}</button>
                <button type="button" className="model-action" aria-pressed={activeIsolated} title={activeIsolated ? 'Show all parts' : 'Show only this part'} onClick={() => isolatePart(isolationKeep, modelUuids)}>{activeIsolated ? 'Show all' : 'Isolate'}</button>
              </div>
            </div>

            <div className="control-block-head">
              <span className="control-sublabel color-label">Auto-rotate</span>
              <button type="button" className="control-button secondary-action play-button" aria-pressed={!!spin} onClick={() => toggleAutoSpin(activePart.uuid)}>
                <Icon name={spin ? 'pause' : 'play'} />
                <span>{spin ? 'On' : 'Off'}</span>
              </button>
            </div>
            {spin && (
              <div className="auto-config">
                <label className="select-field axis-field">
                  <span className="visually-hidden">Auto-rotate axis</span>
                  <select value={spin.axis} onChange={(event) => setAutoSpinAxis(activePart.uuid, Number(event.currentTarget.value) as 0 | 1 | 2)}>
                    <option value={0}>X axis</option>
                    <option value={1}>Y axis</option>
                    <option value={2}>Z axis</option>
                  </select>
                </label>
                <RangeField label="Speed" value={spin.speed} min={0.1} max={5} step={0.1} unit=" rad/s" onChange={(value) => setAutoSpinSpeed(activePart.uuid, value)} />
              </div>
            )}

            <p className="control-sublabel">Rotation (°)</p>
            {axisLabels.map((axisLabel, axis) => (
              <RangeField
                key={`rot-${axisLabel}`}
                label={axisLabel}
                value={transform.rotation[axis]}
                min={-180}
                max={180}
                step={1}
                unit="°"
                onChange={(value) => setPartRotation(activePart.uuid, axis as 0 | 1 | 2, value)}
              />
            ))}
            <p className="control-sublabel">Position</p>
            {axisLabels.map((axisLabel, axis) => (
              <RangeField
                key={`pos-${axisLabel}`}
                label={axisLabel}
                value={transform.position[axis]}
                min={-posRange}
                max={posRange}
                step={posStep}
                onChange={(value) => setPartPosition(activePart.uuid, axis as 0 | 1 | 2, value)}
              />
            ))}
          </>
        ) : (
          <p className="control-hint">Select a part in the model list to set its joint angle, color, and motion.</p>
        )}
      </div>
    </section>
  );
}

function RangeField({ label, value, min, max, step, unit, onChange }: { label: string; value: number; min: number; max: number; step: number; unit?: string; onChange: (value: number) => void }) {
  const display = Math.abs(value) >= 100 || Number.isInteger(value) ? value.toFixed(0) : value.toFixed(2);
  return (
    <label className="range-field">
      <span className="range-head">
        <span className="range-label">{label}</span>
        <span className="range-value">{display}{unit ?? ''}</span>
      </span>
      <input type="range" min={min} max={max} step={step} value={value} onChange={(event) => onChange(Number(event.currentTarget.value))} aria-label={`${label} ${unit ?? ''}`.trim()} />
    </label>
  );
}

function PanelHeader({ icon, eyebrow, title, side, onCollapse }: { icon: IconName; eyebrow: string; title: string; side: 'left' | 'right'; onCollapse: () => void }) {
  return (
    <div className="panel-header">
      <span className="panel-icon"><Icon name={icon} /></span>
      <div className="panel-heading">
        <p>{eyebrow}</p>
        <h2>{title}</h2>
      </div>
      <button type="button" className="panel-collapse" onClick={onCollapse} aria-label={`Collapse ${title} panel`} title="Collapse panel">
        <Icon name={side === 'left' ? 'chevron-left' : 'chevron-right'} />
      </button>
    </div>
  );
}

function PropertyRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>{value}</dd>
    </div>
  );
}

function StatusIcon({ state }: { state: 'idle' | 'loading' | 'ready' | 'error' }) {
  if (state === 'loading') return <span className="spinner" aria-hidden="true" />;
  if (state === 'ready') return <Icon name="check" />;
  if (state === 'error') return <Icon name="alert" />;
  return <Icon name="cube" />;
}

type IconName =
  | 'upload' | 'cube' | 'step' | 'shaded' | 'wireframe' | 'overlay' | 'xray' | 'normals' | 'points'
  | 'top' | 'bottom' | 'front' | 'back' | 'left' | 'right' | 'isometric' | 'fit' | 'reset'
  | 'scene' | 'properties' | 'check' | 'alert' | 'eye' | 'eye-off' | 'chevron-left' | 'chevron-right'
  | 'play' | 'pause' | 'joint' | 'overlap' | 'search' | 'folder';

function Icon({ name }: { name: IconName }) {
  const common = { width: 17, height: 17, viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', strokeWidth: 1.7, strokeLinecap: 'round' as const, strokeLinejoin: 'round' as const, 'aria-hidden': true };

  if (name === 'upload') return <svg {...common}><path d="M12 15V4" /><path d="m7.5 8.5 4.5-4.5 4.5 4.5" /><path d="M4 15v3.5A1.5 1.5 0 0 0 5.5 20h13a1.5 1.5 0 0 0 1.5-1.5V15" /></svg>;
  if (name === 'cube') return <svg {...common}><path d="m12 3 7.5 4.25v8.5L12 20 4.5 15.75v-8.5L12 3Z" /><path d="M12 11.5 4.8 7.4" /><path d="m12 11.5 7.2-4.1" /><path d="M12 11.5V20" /></svg>;
  if (name === 'search') return <svg {...common}><circle cx="11" cy="11" r="6" /><path d="m16 16 4 4" /></svg>;
  if (name === 'folder') return <svg {...common}><path d="M3.5 7.5a2 2 0 0 1 2-2h4l2 2h7a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2h-13a2 2 0 0 1-2-2v-9Z" /><path d="M3.5 9.5h17" /></svg>;
  if (name === 'step') return <svg {...common}><path d="M4 16.5 12 21l8-4.5" /><path d="M4 12.5 12 17l8-4.5" /><path d="M4 8.5 12 13l8-4.5L12 4 4 8.5Z" /><path d="M8 10.8h8" /></svg>;
  if (name === 'shaded') return <svg {...common}><path d="M5 7.5 12 4l7 3.5v9L12 20l-7-3.5v-9Z" fill="currentColor" fillOpacity="0.18" /><path d="M12 4v16" /><path d="m5 7.5 7 3.5 7-3.5" /></svg>;
  if (name === 'wireframe') return <svg {...common}><path d="M5 7.5 12 4l7 3.5v9L12 20l-7-3.5v-9Z" /><path d="M12 4v16" /><path d="m5 7.5 7 3.5 7-3.5" /><path d="m5 16.5 7-5.5 7 5.5" /></svg>;
  if (name === 'overlay') return <svg {...common}><path d="M5 7.5 12 4l7 3.5v9L12 20l-7-3.5v-9Z" fill="currentColor" fillOpacity="0.14" /><path d="M5 7.5h14" /><path d="M5 12h14" /><path d="M5 16.5h14" /></svg>;
  if (name === 'xray') return <svg {...common}><path d="M4 12s3-5.5 8-5.5S20 12 20 12s-3 5.5-8 5.5S4 12 4 12Z" /><circle cx="12" cy="12" r="2.4" /><path d="M7 19 17 5" /></svg>;
  if (name === 'normals') return <svg {...common}><path d="M5 17 11 5l8 14H6.5" /><path d="M11 5v8" /><path d="m8.5 10.5 2.5 2.5 2.5-2.5" /></svg>;
  if (name === 'points') return <svg {...common}><circle cx="6" cy="7" r="1.4" /><circle cx="15.5" cy="5.5" r="1.4" /><circle cx="18" cy="14" r="1.4" /><circle cx="10" cy="18" r="1.4" /><circle cx="5" cy="14" r="1.4" /><path d="m6 7 9.5-1.5L18 14l-8 4-5-4 1-7Z" /></svg>;
  if (name === 'top') return <svg {...common}><path d="M12 4v13" /><path d="m7 9 5-5 5 5" /><path d="M5 20h14" /></svg>;
  if (name === 'bottom') return <svg {...common}><path d="M12 20V7" /><path d="m7 15 5 5 5-5" /><path d="M5 4h14" /></svg>;
  if (name === 'front') return <svg {...common}><rect x="5" y="5" width="14" height="14" rx="2" /><path d="M9 9h6v6H9z" /></svg>;
  if (name === 'back') return <svg {...common}><rect x="5" y="5" width="14" height="14" rx="2" /><path d="M8 8h8v8H8z" strokeDasharray="2 2" /></svg>;
  if (name === 'left') return <svg {...common}><path d="M14 5 7 12l7 7" /><path d="M8 12h10" /></svg>;
  if (name === 'right') return <svg {...common}><path d="m10 5 7 7-7 7" /><path d="M6 12h10" /></svg>;
  if (name === 'isometric') return <svg {...common}><path d="m12 3 7.5 4.25v8.5L12 20 4.5 15.75v-8.5L12 3Z" /><path d="M12 11.5V20" /><path d="M4.8 7.4 12 11.5l7.2-4.1" /></svg>;
  if (name === 'fit') return <svg {...common}><path d="M8 4H4v4" /><path d="M16 4h4v4" /><path d="M8 20H4v-4" /><path d="M16 20h4v-4" /><path d="M9 9h6v6H9z" /></svg>;
  if (name === 'reset') return <svg {...common}><path d="M4.5 12a7.5 7.5 0 1 0 2.2-5.3" /><path d="M4.5 5.5v4h4" /></svg>;
  if (name === 'scene') return <svg {...common}><path d="M6 5h6" /><path d="M6 12h12" /><path d="M6 19h9" /><circle cx="4" cy="5" r="1" /><circle cx="4" cy="12" r="1" /><circle cx="4" cy="19" r="1" /></svg>;
  if (name === 'properties') return <svg {...common}><path d="M5 5h14" /><path d="M5 12h14" /><path d="M5 19h14" /><path d="M9 5v4" /><path d="M15 12v4" /><path d="M11 19v-4" /></svg>;
  if (name === 'check') return <svg {...common}><path d="m5 12 4.2 4L19 6" /></svg>;
  if (name === 'eye') return <svg {...common}><path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z" /><circle cx="12" cy="12" r="3" /></svg>;
  if (name === 'eye-off') return <svg {...common}><path d="M10.6 6.1A9.8 9.8 0 0 1 12 6c6 0 9.5 6 9.5 6a17.3 17.3 0 0 1-2.4 3" /><path d="M6.3 6.3A16.7 16.7 0 0 0 2.5 12S6 18 12 18a9.4 9.4 0 0 0 4-.9" /><path d="m4 4 16 16" /><path d="M9.9 9.9a3 3 0 0 0 4.2 4.2" /></svg>;
  if (name === 'chevron-left') return <svg {...common}><path d="m14 6-6 6 6 6" /></svg>;
  if (name === 'chevron-right') return <svg {...common}><path d="m10 6 6 6-6 6" /></svg>;
  if (name === 'play') return <svg {...common}><path d="M8 5.5v13l10-6.5-10-6.5Z" fill="currentColor" fillOpacity="0.25" /></svg>;
  if (name === 'pause') return <svg {...common}><path d="M8 5h3v14H8z" /><path d="M14 5h3v14h-3z" /></svg>;
  if (name === 'joint') return <svg {...common}><circle cx="6" cy="18" r="2.4" /><circle cx="18" cy="6" r="2.4" /><path d="M7.7 16.3 16 8" /><path d="M5 11V7a2 2 0 0 1 2-2h3" /></svg>;
  if (name === 'overlap') return <svg {...common}><rect x="4" y="4" width="11" height="11" rx="1.5" /><rect x="9" y="9" width="11" height="11" rx="1.5" /></svg>;
  return <svg {...common}><path d="M12 8v5" /><path d="M12 17h.01" /><path d="M10.3 4.4 3.4 17a2 2 0 0 0 1.8 3h13.6a2 2 0 0 0 1.8-3L13.7 4.4a2 2 0 0 0-3.4 0Z" /></svg>;
}
