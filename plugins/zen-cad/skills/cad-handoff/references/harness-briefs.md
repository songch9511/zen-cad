# Harness Briefs

## Codex

Use this when Codex will create or edit source files:

```text
Use the CAD spec below to create a low-detail layout proxy first.
Preserve locked facts exactly.
Use named parameters for critical dimensions, clearances, and motion controls.
Use the available CAD stack in this workspace.
Before editing geometry, write a Subagent Dispatch Plan for layout, interface, parameter, motion, CAD generation, visual review, engineering review, CAD review, and repair. Spawn bounded subagents when available; otherwise state `Subagent status: unavailable; using sequential fallback roles`.
Return source path, primary CAD artifact path, checks run, failed or skipped checks, and limitations.
Return source-of-truth, generated files, repair attempts, and claims not made.
If viewer or screenshot tooling is available, capture multi-view evidence and inspect fastening, clearance, floating body, interference, mesh/alignment, and engineering plausibility concerns.
Convert visual concerns into measurable checks before claiming they are fixed.
If a check fails, make the smallest responsible source-level repair, regenerate, and rerun the failed check.
Do not claim final engineering validity.
```

## text-to-cad / $cad

Use this when the `earthtojake/text-to-cad` CAD skill is installed:

```text
Use $cad to generate STEP-first CAD from this CAD-native spec.
Create build123d/Python source when generating new geometry.
Use named parameters, datums, labels, and source-level joints where useful.
Run deterministic geometry inspection first: refs/facts/planes/positioning plus targeted measure, frame, mate, or diff checks when relevant.
If visible primary CAD was created or updated and snapshot/viewer tooling is available, return saved snapshots or viewer links; if skipped, state why.
Inspect snapshots for floating bodies, unintended interference, insufficient clearance, missing fastener engagement, shaft/bore or bearing misalignment, belt/gear mesh errors, and implausible support/load paths.
For each visual concern, add or name a measurable check and repair the smallest source-level cause before final response.
Do not treat viewer links or screenshots as substitutes for geometry checks.
Repair the smallest source-level cause of any failed check, then regenerate and rerun dependent checks.
Hand supported artifacts to $cad-viewer when available.
Stop instead of changing locked layout facts.
```

When a Zen CAD `handoff_packet` already exists from an approved proceed gate and the target is CAD Skills/text-to-cad, package the downstream prompt bundle instead of running the build123d generator:

```bash
python3 tools/package_text_to_cad_bundle.py --handoff <detail_handoff.json> --out <text-to-cad-bundle-dir>
```

Send `text_to_cad_prompt.md` and `handoff_packet.json` to CAD Skills/text-to-cad. The bundle manifest records that the text-to-cad adapter step did not create CAD source, STEP/STP geometry, snapshots, or viewer links.

## build123d

Use this when Zen CAD should generate a first-pass STEP artifact locally:

```bash
python3 tools/run_contract_pipeline.py --package <contract-package> --out <run-dir> --target-harness build123d
```

The runner exports `source/layout_proxy_build123d.py`, carries any native `cad_feature_plan` into the source, executes `gen_step()`, writes `source/layout_proxy_build123d.step`, re-imports the STEP, records export/import/bbox/volume and feature-plan checks in `source/cad_generation.inspection_report.json`, and writes `viewer_link.html` for local review. When CAD-Visualizer is available, run the runner with `--capture-viewer-snapshot --viewer-root <viewer-root>` so the proceed gate includes review evidence. Treat that evidence as a prompt for measurable repair checks, not final proof.

## Generic CAD Generator

Use when the toolchain is unknown:

```text
Generate a low-detail assembly layout from this spec.
Use simple solids for proxies.
Preserve coordinate frames, axes, center distances, mounting faces, pitch references, clearances, and motion relationships.
Before editing geometry, write a Subagent Dispatch Plan. If subagents are unavailable, state `Subagent status: unavailable; using sequential fallback roles` and run layout, interface, parameter, motion, CAD generation, visual review, engineering review, CAD review, and repair sequentially.
If viewer or screenshot tooling exists, inspect generated evidence for floating bodies, unintended interference, insufficient clearance, missing fastener engagement, shaft/bore or bearing misalignment, belt/gear mesh errors, and implausible support/load paths.
For each visual concern, add or name a measurable check and repair the smallest source-level cause before final response.
Use named parameters and return the primary artifact path, inspection evidence, skipped checks, and limitations.
State generated files as derived artifacts and identify the source/spec as authoritative.
Report any missing information instead of inventing final details.
```
