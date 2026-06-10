# Generic Usage

Zen CAD 1.0 can be used in any agentic environment that can read Markdown and hand work to a CAD-generation toolchain. The product version is 1.0.1, while contract documents continue to use `schema_version: 0.8.0` for compatibility.

Start with:

```text
Use skills/cad-spec/SKILL.md to write a CAD-native spec for: <goal>
```

When installed as a Codex plugin, use `/cad-spec` directly. Project connection alone does not
register slash skills; install the local `zen-cad` plugin from `.codex-plugin/marketplace.json`
and start a new chat after installation.

If the user asks to continue into CAD generation, keep `cad-spec` as the lead workflow and delegate bounded specialist tasks when the harness supports subagents:

- layout contract review;
- parameter contract review;
- interface signature extraction;
- motion and drivetrain relationship checks;
- layout proxy generation;
- generated artifact inspection;
- repair-loop review;
- generated CAD review against locked facts.

Use `skills/cad-handoff/SKILL.md` when the active generator needs a concise task brief. If the active target is build123d and local dependencies are available, Zen CAD can generate a first-pass STEP artifact itself before the proceed review. Contract packages can include `cad_spec.extensions.cad_feature_plan` when native generation should preserve holes, bores, repeated hole patterns, rectangular top chamfers, simplified gear teeth, or supported cylinder edge-round approximations.

Use `schemas/` when a harness needs machine-readable contracts, and use `registry/interfaces/` when a layout proxy needs known component interface facts without catalog crawling. For final-stage standard/catalog part sourcing, use `schemas/source_lock_evidence.schema.json` and `tools/generate_source_lock_evidence.py` to record explicit step.parts, manufacturer, datasheet, project-file, or user-provided evidence separately from layout interface signatures. Use `tools/download_step_part.py` when a step.parts match should be downloaded, sha256-verified, and written as local source-lock evidence. When that evidence includes a STEP/STP geometry reference, `tools/export_cad_source.py` imports the sourced part into generated build123d source and removes the matching proxy primitives.

Run the contract pipeline runner after a contract package exists. Use `--target-harness build123d` when Zen CAD should execute the generated source and write a STEP artifact locally:

```bash
python3 tools/run_contract_pipeline.py --package <path> --out <dir> --target-harness build123d
```

The runner verifies the built-in schema and registry surface, validates the package, creates a kernel-neutral `layout_proxy.scene.json`, inspects scene carry-through, exports CAD source intent, imports source-locked STEP/STP parts when geometry references exist, inspects source carry-through, executes generated build123d source into a primary STEP artifact when the target is `build123d`, packages a local viewer link, optionally captures a viewer PNG snapshot, packages proceed review, and writes a machine-readable `review_bundle.json`.

To make the viewer link auto-load in CAD-Visualizer, run the viewer on `http://localhost:5173` and give the runner the Vite public directory:

```bash
python3 tools/run_contract_pipeline.py --package <path> --out <dir> --target-harness build123d --viewer-base-url http://localhost:5173 --viewer-public-dir /Users/daniel/CAD-Visualizer/public
```

To also capture a review snapshot through CAD-Visualizer, pass the viewer project root:

```bash
python3 tools/run_contract_pipeline.py --package <path> --out <dir> --target-harness build123d --viewer-base-url http://localhost:5173 --viewer-public-dir /Users/daniel/CAD-Visualizer/public --capture-viewer-snapshot --viewer-root /Users/daniel/CAD-Visualizer
```

The build123d generation phase can also be run directly:

```bash
python3 tools/generate_cad_artifact.py --source <dir>/source/layout_proxy_build123d.py --manifest <dir>/source/cad_source_manifest.json
```

This performs source import, `gen_step()`, STEP export, STEP re-import, validity, bounding-box, and volume checks. It is still a first-pass CAD artifact, not manufacturing certification.

Native benchmark packages are available under `benchmarks/` for regression and prompt calibration:

- `benchmarks/01-rectangular-calibration-block/package`;
- `benchmarks/02-circular-flange/package`;
- `benchmarks/03-planetary-gear-stage/package`.

For a viewer-oriented downstream review, package the proceed gate into a Markdown brief:

```bash
python3 tools/package_viewer_review.py --proceed-gate <dir>/proceed_gate.json --pipeline-run <dir>/pipeline_run.json --out <dir>/viewer_review.md
```

Add `--viewer-artifact <path>` for saved screenshots, viewer pages, GLB/STL/3MF models, or viewer-side reports. The brief treats those files as review aids only; completion evidence still comes from the proceed gate status, inspection reports, locked facts, and downstream geometry measurements.

After the user approves the layout, record the decision and run the detail handoff stage:

```bash
python3 tools/approve_proceed_gate.py --proceed-gate <dir>/proceed_gate.json --out <approval.json>
python3 tools/run_contract_pipeline.py --package <path> --out <detail-dir> --target-harness text-to-cad --approval <approval.json>
python3 tools/package_text_to_cad_bundle.py --handoff <detail-dir>/detail_handoff.json --out <text-to-cad-bundle-dir>
```

For CAD Skills/text-to-cad, the bundle contains `text_to_cad_prompt.md`, `handoff_packet.json`, and `adapter_manifest.json`. The bundle is a downstream contract and prompt only; CAD source, STEP export, geometry checks, snapshots, and viewer links remain text-to-cad responsibilities.

The phase tools remain available for focused diagnosis:

- `tools/validate_contract.py`;
- `tools/generate_layout_proxy.py`;
- `tools/inspect_layout_proxy.py`;
- `tools/export_cad_source.py`;
- `tools/inspect_cad_source.py`;
- `tools/generate_cad_artifact.py`;
- `tools/package_viewer_link.py`;
- `tools/capture_viewer_snapshot.py`;
- `tools/package_proceed_gate.py`;
- `tools/package_review_bundle.py`;
- `tools/package_viewer_review.py`;
- `tools/approve_proceed_gate.py`;
- `tools/generate_detail_handoff.py`;
- `tools/package_text_to_cad_bundle.py`;
- `tools/generate_source_lock_evidence.py`;
- `tools/download_step_part.py`.

These tools keep the contract layer explicit while adding a build123d generation path. They do not replace advanced topology inspection, source-locked supplier geometry alignment checks, manufacturing review, or engineering certification. Viewer links and snapshots are review aids only.
