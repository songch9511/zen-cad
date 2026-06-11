# Zen CAD

Assembly-first CAD contract runtime for mechanical design agents.

[![Version](https://img.shields.io/badge/version-1.0.2-4A5568?style=for-the-badge)](VERSION)
[![1.0 Line](https://img.shields.io/badge/1.0--line-source--lock-00A676?style=for-the-badge)](CHANGELOG.md)
[![Assembly First](https://img.shields.io/badge/assembly--first-layout-2F80ED?style=for-the-badge)](skills/assembly-layout/SKILL.md)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

Zen CAD helps Codex-style agents turn natural-language mechanical design requests into inspectable CAD work. It is built around a simple rule: lock the mechanical intent before polishing geometry.

The workflow starts with a CAD-native spec, then preserves frames, datums, axes, bores, shafts, bolt patterns, pitch references, clearances, motion relationships, and source evidence through layout, generation, review, and handoff artifacts.

## Current Version

- Product/plugin version: `1.0.2`
- Contract schema version: `0.8.0`
- Primary local generation target: `build123d`
- Review target: generated STEP plus optional CAD-Visualizer link/snapshot
- Evidence priority: measurable geometry checks first, visual review second, prose caveats last

## What It Does

- Converts mechanical prompts into CAD-native specs.
- Builds machine-readable contract packages for layout, interfaces, inspection, proceed review, and handoff.
- Generates first-pass build123d STEP artifacts when local dependencies are available.
- Preserves feature intent for holes, bores, repeated hole patterns, chamfers, supported fillet approximations, and simplified gear teeth.
- Imports verified source-locked STEP/STP parts into generated build123d source when explicit evidence exists.
- Packages local CAD-Visualizer review links and optional PNG snapshots.
- Guides visual and engineering review for floating bodies, interference, clearance, fastening, alignment, mesh/contact, and implausible support paths.

## What It Does Not Do

- It does not replace a CAD kernel, CAE solver, manufacturing review, or certification process.
- It does not guarantee supplier SKU correctness, inventory, ratings, or compliance claims.
- It does not crawl broad catalogs by itself.
- It does not treat screenshots as proof of completion.
- It does not force a specific subagent runtime. When subagents are available, the skills ask for a dispatch plan; otherwise the lead agent runs the same review roles sequentially.

## Workflow

1. Write a CAD-native spec with locked parameters, frames, interfaces, and inspection targets.
2. Generate a kernel-neutral layout proxy and inspect whether locked facts survived.
3. Export build123d source and inspect source-level carry-through.
4. Generate a STEP artifact when `build123d` is available.
5. Package a proceed gate with inspection reports, generated artifacts, and optional viewer evidence.
6. Review visually and mechanically, repair the smallest source-level cause, then regenerate.
7. After user approval, create a downstream detail handoff.

## Codex Usage

Install the local plugin bundle from [`plugins/zen-cad`](plugins/zen-cad). Connecting the folder as a project is not enough to register slash skills.

After installation and a new chat, the main entrypoints are:

- `/cad-spec`
- `/assembly-layout`
- `/interface-signatures`
- `/cad-handoff`

Plain prompt usage also works when the project instructions are loaded:

```text
Use skills/cad-spec/SKILL.md to create a CAD-native spec for:
Create a flat planetary gear assembly with separate sun, planet, ring, carrier, and pin bodies. Use simplified trapezoidal teeth and place three planets around the sun on a 42 mm radius circle.
```

For generation and review work, a useful lead instruction is:

```text
Create the CAD-native spec, generate the first-pass STEP if the local harness supports it, inspect the result visually and mechanically, repair source-level issues, and package the proceed gate. Use specialist subagents if available; otherwise run the same review roles sequentially.
```

## Command Flow

Run a full local build123d pipeline:

```bash
python3 tools/run_contract_pipeline.py --package <contract-package> --out <run-dir> --target-harness build123d
```

Create a CAD-Visualizer link for `http://localhost:5173`:

```bash
python3 tools/run_contract_pipeline.py --package <contract-package> --out <run-dir> --target-harness build123d --viewer-base-url http://localhost:5173 --viewer-public-dir /Users/daniel/CAD-Visualizer/public
```

Capture a viewer snapshot as review evidence:

```bash
python3 tools/run_contract_pipeline.py --package <contract-package> --out <run-dir> --target-harness build123d --viewer-base-url http://localhost:5173 --viewer-public-dir /Users/daniel/CAD-Visualizer/public --capture-viewer-snapshot --viewer-root /Users/daniel/CAD-Visualizer
```

Approve a proceed gate and create a detail handoff:

```bash
python3 tools/approve_proceed_gate.py --proceed-gate <run-dir>/proceed_gate.json --out <approval.json>
python3 tools/run_contract_pipeline.py --package <contract-package> --out <detail-run-dir> --target-harness text-to-cad --approval <approval.json>
```

Download and lock an explicit step.parts source:

```bash
python3 tools/download_step_part.py --id <step-parts-id> --download --out-dir <contract-package>/sourced_parts/step_parts --package <contract-package> --part-id <part-id> --source-lock-out <contract-package>/<part-id>_source_lock.json
```

## Native Benchmarks

Curated benchmark packages live under [`benchmarks/`](benchmarks):

- rectangular calibration block
- circular flange
- simplified planetary gear stage

They are intentionally small enough for regression checks, but they cover the features Zen CAD currently needs to preserve: through-holes, bores, bolt circles, chamfers, edge-round approximations, separate bodies, and repeated gear-like teeth.

## Visual Review And Repair

Zen CAD 1.0.2 adds skill guidance for agent-visible repair loops. The goal is not physical simulation. The goal is to make the agent look at the generated CAD, name the mechanical issue, connect it to a measurable contract check, repair the source, and regenerate.

Review should explicitly look for:

- floating or unsupported bodies;
- unintended intersections;
- insufficient clearance;
- missing fastener engagement;
- shaft, bore, bearing, and pulley misalignment;
- belt, gear, or contact-plane mismatch;
- weak or implausible load paths.

Viewer screenshots are useful review artifacts, but completion still depends on geometry reports, locked facts, inspection checks, and user approval.

## Repository Map

- [`skills/`](skills): agent-facing workflows.
- [`schemas/`](schemas): machine-readable contract surfaces.
- [`registry/interfaces/`](registry/interfaces): layout-ready interface facts.
- [`tools/run_contract_pipeline.py`](tools/run_contract_pipeline.py): one-command pipeline runner.
- [`tools/generate_cad_artifact.py`](tools/generate_cad_artifact.py): build123d STEP generation and inspection.
- [`tools/download_step_part.py`](tools/download_step_part.py): step.parts download and checksum-backed source-lock evidence.
- [`tools/package_viewer_link.py`](tools/package_viewer_link.py): CAD-Visualizer link packaging.
- [`tools/capture_viewer_snapshot.py`](tools/capture_viewer_snapshot.py): optional viewer PNG capture.

## Development Checks

```bash
python3 tools/validate_contract.py
python3 -m unittest discover -s tests
python3 -m py_compile tools/*.py tests/*.py
```

Temporary project runs stay under ignored run directories such as `work/`. Curated benchmark contracts stay under [`benchmarks/`](benchmarks).
