---
name: spec-to-cad
description: Milestone-first CAD execution skill for turning measurable mechanical specs into STEP-first CAD artifacts with command-backed Zen CAD validation evidence.
version: 0.6.6
---

# Spec-to-CAD

## Purpose

`/spec-to-cad` is the downstream CAD execution skill for Zen CAD. It receives a measurable handoff from `/agentic-cad`, creates or updates design-specific CAD, and records the command-backed evidence needed for Zen CAD completion gates.

The central rule is: **produce a real CAD artifact first, then grade it honestly**. Concept/layout work may be incomplete or environment-blocked. Final/release work must produce reproducible validation evidence, not a screenshot, worker summary, or metadata-only PASS.

When `earthtojake/text-to-cad` or an equivalent STEP-first CAD skill is available, use it as the preferred generation, inspection, and snapshot path. Zen CAD wraps that execution with milestone structure, source-lock rules, artifact hashes, BOM, and reporting.

## Root Model

Keep these paths explicit:

- **Zen CAD repository root**: the checkout containing `./zen-cad`, `skills/`, `schemas/`, and `milestones/`.
- **Active milestone**: `milestones/<id>/`.
- **CAD source directory**: usually `milestones/<id>/03_cad/`.
- **Validation directory**: `milestones/<id>/05_validation/`.

If this skill is installed into CoBrA and a sibling `ZEN_CAD_WORKSPACE.md` exists, read its `Repository root:` line and use that checkout unless the user gives another root. In Codex, Claude Code, or another repo-local harness, use the current repository root.

Do not create project artifacts in unrelated workspace paths. All Zen CAD milestone artifacts should stay under the active milestone unless the user explicitly asks for a separate export location.

## Use This Skill When

Use `/spec-to-cad` when the task needs:

- generated or modified mechanical CAD source;
- STEP/STP as the primary CAD artifact;
- STL, 3MF, DXF, GLB, or snapshots as secondary artifacts;
- assembly contact or connection evidence;
- source-level custom parts that integrate sourced STEP parts;
- validation evidence for `./zen-cad validate --level completion`.

Do not use this skill to generate final lookalikes for standard/catalog parts. If a part is classified as `off_the_shelf` or source-first `semi_standard_configurable`, use its source-locked STEP/STP file or return a blocker.

## Default Workflow

1. Resolve the Zen CAD root and active milestone.
2. Read the measurable handoff from `03_cad/custom_cad_handoff.yaml`, requirements, selected parts manifest, CONTACT_MAP, and CONNECTIONS.
3. Decide whether the milestone is `concept`, `layout`, or `final`.
4. Generate or update design-specific CAD source under `03_cad/`.
5. Produce explicit STEP/STP output targets. Prefer STEP as the primary artifact.
6. Inspect geometry deterministically. Prefer text-to-cad `scripts/inspect refs --facts --planes --positioning`, then targeted `measure`, `mate`, `frame`, or `diff` where relevant.
7. Run snapshot review for visible primary STEP/STP changes when the CAD stack supports it. Snapshots are human review only.
8. Record command-backed validation evidence in `05_validation/validation_report.json`.
9. Link CONTACT_MAP and CONNECTIONS rows to passing geometry checks with `evidence_check_ids`.
10. Run `./zen-cad validate --level structure milestones/<id>` for concept/layout and `./zen-cad validate --level completion milestones/<id>` before any final claim.

## Preferred text-to-cad Path

When the text-to-cad CAD skill is installed, use its launchers from that skill directory or the harness-provided equivalent:

```bash
python scripts/step <generator.py>
python scripts/inspect refs <model.step> --facts --planes --positioning
python scripts/inspect measure --from '@cad[<model.step>#selector_a]' --to '@cad[<model.step>#selector_b]' --axis z
python scripts/inspect mate --moving '@cad[<model.step>#moving_selector]' --target '@cad[<model.step>#target_selector]' --mode flush --axis z
python scripts/inspect frame '@cad[<model.step>#selector]'
python scripts/inspect diff <before.step> <after.step> --planes
python scripts/snapshot <model.step>
```

Adapt launcher paths to the installed skill location. Use absolute target paths when the CAD skill directory and Zen CAD repository are different directories.

Expected text-to-cad evidence:

- explicit target generation command, not directory-wide generation;
- primary STEP/STP path;
- generated sidecar paths when produced;
- refs/facts/planes/positioning output;
- targeted measure/mate/frame/diff output when relevant;
- snapshot PNG/GIF paths or a documented skip reason;
- any selectors used in CONTACT_MAP or CONNECTIONS.

If text-to-cad is unavailable, use build123d, CadQuery, FreeCAD, OpenSCAD, or another kernel-backed stack. The validation evidence contract remains the same.

Use `/cad-artifact-reviewer` after generation when a final/release claim is being made. Use `/mechanism-kinematics` before or during generation when the assembly needs explicit joints, frames, axes, travel, or URDF/SDF/SRDF handoff data.

## Milestone Artifact Paths

Use the repo's canonical milestone layout:

```text
milestones/<id>/
├─ 00_requirements/requirements_brief.md
├─ 01_research/research_log.md
├─ 02_parts/part_classification_table.md
├─ 02_parts/selected_parts_manifest.json
├─ 03_cad/custom_cad_handoff.yaml
├─ 03_cad/<cad_source>
├─ 03_cad/exports/<primary>.step
├─ 04_assembly/contact_map.json
├─ 04_assembly/connections.json
├─ 05_validation/validation_report.json
├─ 06_bom/bom.csv
└─ 07_report/final_engineering_report.md
```

Do not invent parallel root-level files such as `requirements.md`, `CONTACT_MAP.json`, or `BOM.csv` when working inside a Zen CAD milestone.

## CAD Source Requirements

For custom CAD source:

- use named parameters and units;
- keep output paths explicit;
- keep source and derived exports traceable;
- generate closed positive-volume solids unless the spec asks for surfaces;
- name major bodies/features where the CAD stack supports labels;
- define assembly datums, frames, or transforms in source, not only in narrative text;
- avoid proxy-only geometry for final evidence.

For sourced standard parts:

- never regenerate the catalog part as final evidence;
- use the cached STEP/STP from `02_parts/selected_parts_manifest.json`;
- record missing or unusable source files as blockers.

## Validation Evidence Contract

For final completion, `05_validation/validation_report.json` must pass the Zen CAD schema and completion gate audit. A PASS report needs passing checks with:

- `evidence_type`;
- `command.argv`, `command.cwd`, and `command.exit_code`;
- `artifacts[]` with `path`, `role`, `size_bytes`, and `sha256`;
- a truthful `limitations` list.

Required final evidence types:

- `cad_generation`;
- `step_load`;
- `geometry_inspection`.

If the local validator cannot pass `./zen-cad doctor --cad-required`, include a passing `environment` evidence check from the CAD runtime that actually generated the final artifacts. Otherwise report the final gate as BLOCKED.

Minimal final check shape:

```json
{
  "check_id": "CHK-002",
  "name": "STEP-first CAD generation",
  "result": "pass",
  "evidence_type": "cad_generation",
  "evidence": "Generated primary STEP from the recorded CAD source.",
  "command": {
    "argv": ["python", "scripts/step", "milestones/<id>/03_cad/<source.py>"],
    "cwd": "<cad-skill-or-repo-root>",
    "exit_code": 0
  },
  "artifacts": [
    {
      "path": "03_cad/<source.py>",
      "role": "cad_source",
      "size_bytes": 1234,
      "sha256": "<sha256>"
    },
    {
      "path": "03_cad/exports/<model>.step",
      "role": "primary_step",
      "size_bytes": 5678,
      "sha256": "<sha256>"
    }
  ],
  "limitations": []
}
```

STEP evidence must verify at least:

- file exists and is non-empty;
- file hash and size match the validation report;
- STEP/STP file terminates with `END-ISO-10303-21`;
- when a kernel is available, the file loads through the selected kernel or text-to-cad inspect path.

Geometry inspection evidence should record:

- bounding box, units, scale, and major labels/refs;
- critical dimensions and offsets;
- assembly references, frames, or positioning where relevant;
- contact/clearance/mate measurements where in scope;
- explicit limitations for checks not run.

## CONTACT_MAP and CONNECTIONS

For every contact or connection row that supports a final claim:

- reference actual part ids from `selected_parts_manifest.json`;
- include CAD selectors or refs when available;
- include expected clearance, mate, fastener, or contact intent;
- add `evidence_check_ids` pointing to passing validation checks.

Example:

```json
{
  "contact_id": "CT-001",
  "part_a": "C-001",
  "part_b": "P-001",
  "type": "mounting_face",
  "expected_clearance_mm": 0.0,
  "cad_refs": [
    "@cad[03_cad/exports/assembly.step#custom_plate_top]",
    "@cad[02_parts/step/P-001.step#mounting_face]"
  ],
  "evidence_check_ids": ["CHK-004"],
  "notes": "Flush motor-face interface verified by geometry inspection."
}
```

## Concept/Layout vs Final

For `concept` or `layout` maturity:

- generate useful CAD early with the available toolchain;
- record source/export paths and assumptions;
- keep proxy parts and missing source-locks explicit;
- run `./zen-cad validate --level structure milestones/<id>`;
- report final blockers instead of claiming completion.

For `final` maturity:

- run or record source-lock evidence;
- produce primary STEP/STP and required secondary exports;
- hash-lock validation artifacts;
- link assembly rows to geometry evidence;
- run `./zen-cad validate --level completion milestones/<id>`;
- only claim final completion if the command passes.

## Failure Handling

When generation or validation fails:

1. Preserve the failed command and error.
2. Classify the blocker: environment, source-lock, generation, STEP load, geometry inspection, assembly, BOM/report, or unsupported analysis.
3. Fix the smallest responsible source or metadata section.
4. Regenerate only the affected artifacts.
5. Rerun the failed validation command.
6. If still blocked, write a truthful blocker and smallest unblock step.

Forbidden shortcuts:

- metadata-only PASS;
- stale export PASS;
- hash values copied from another file;
- screenshots as completion evidence;
- generated catalog-part lookalikes as final standard parts;
- CONTACT_MAP/CONNECTIONS rows without evidence links;
- claims of FEA, fatigue, manufacturability, certification, or ratings without the relevant analysis.

## Final Response Contract

When handing results back to the user, include:

- active milestone path;
- CAD source path;
- primary STEP/STP path;
- secondary artifact paths;
- validation commands run;
- PASS/BLOCKED result;
- key dimensions or inspection facts;
- known limitations and unperformed analyses.

Do not imply that CAD validation proves structural safety, manufacturing tolerance, fatigue life, certification, procurement readiness, or physical-test performance.

## Short Form

```text
Resolve Zen CAD root and milestone -> read handoff -> generate design-specific CAD -> prefer text-to-cad scripts/step -> inspect refs/facts/planes/positioning -> measure/mate/frame/diff as needed -> snapshot for visual review -> write validation_report.json with command metadata and artifact hashes -> link CONTACT_MAP/CONNECTIONS evidence_check_ids -> run ./zen-cad validate --level completion before final claims.
```
