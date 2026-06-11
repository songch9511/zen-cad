# Zen CAD Viewer

Repo-local CAD review viewer for Zen CAD generated artifacts.

This starts from the existing Vite/React/Three viewer and moves it under the
Zen CAD repository so the contract pipeline can package review links without
depending on a separate checkout.

## Current Slice

- STEP/STP, STL, OBJ, glTF, and GLB loading.
- In-browser STEP tessellation through OpenCascade WASM.
- Render modes, camera presets, fit/reset controls, scene tree, part visibility,
  part coloring, simple transforms, animation playback, and overlap review.
- Query-string model loading through `?model=/zen-cad-artifacts/<file.step>`.
- Pipeline drop directory at `public/zen-cad-artifacts/`.

## Direction

The target architecture follows the workbench split used by
`earthtojake/text-to-cad/viewer`:

- `viewer/` owns React UI, workbench state, file navigation, panels, and review
  interactions.
- A future viewer runtime package should own CAD parsing, scene construction,
  STEP sidecars, selector data, and render helpers without React dependencies.
- Zen CAD tools should hand the viewer generated STEP, layout scene JSON,
  source manifests, proceed gates, and review bundles from inside this repo.

## Commands

```bash
npm install
npm run dev:local
npm run build
```

The default local URL is `http://localhost:5173`.

## Pipeline Use

For an auto-load review link, pass this viewer's public directory:

```bash
python3 ../tools/run_contract_pipeline.py \
  --package <contract-package> \
  --out <run-dir> \
  --target-harness build123d \
  --viewer-base-url http://localhost:5173 \
  --viewer-public-dir "$(pwd)/public"
```
