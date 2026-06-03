---
name: cad-artifact-reviewer
description: Independently review Zen CAD milestone CAD artifacts, validation reports, STEP/STP exports, hashes, CONTACT_MAP/CONNECTIONS evidence links, and final claims before completion is accepted.
version: 0.6.4
---

# CAD Artifact Reviewer

## Purpose

`/cad-artifact-reviewer` is an independent review skill for Zen CAD milestones. Use it after `/spec-to-cad` produces CAD artifacts and before any final/release claim.

The reviewer does not generate CAD. It checks whether the artifacts and evidence actually support the claimed milestone status.

## Use This Skill When

Use this skill when:

- a milestone is being presented as `final` or release-ready;
- `05_validation/validation_report.json` has been updated;
- STEP/STP exports, STL/3MF/DXF/GLB exports, snapshots, or viewer output need review;
- CONTACT_MAP or CONNECTIONS rows claim geometry evidence;
- a final report or BOM makes claims that may exceed the evidence.

For concept/layout work, use this skill to state visible limitations and final blockers. Do not convert visual review into completion evidence.

## Inputs

Resolve the Zen CAD root and active milestone, then read:

```text
00_requirements/requirements_brief.md
02_parts/selected_parts_manifest.json
02_parts/normalized_step_metadata.json
03_cad/custom_cad_handoff.yaml
03_cad/exports/
04_assembly/contact_map.json
04_assembly/connections.json
05_validation/validation_report.json
06_bom/bom.csv
07_report/final_engineering_report.md
```

Also inspect generated snapshots, viewer links, or inspection JSON files when present.

## Review Procedure

1. Confirm the milestone path and target maturity.
2. Run `./zen-cad validate --level structure milestones/<id>`.
3. If final/release is claimed, run `./zen-cad validate --level completion milestones/<id>`.
4. Verify every reported artifact path exists under the milestone unless an external path is explicitly justified.
5. Recompute file size and SHA-256 for validation artifacts and compare them to `validation_report.json`.
6. Confirm every PASS check has `evidence_type`, `command.argv`, `command.cwd`, `command.exit_code`, `artifacts`, and truthful `limitations`.
7. Confirm required final evidence types are present: `cad_generation`, `step_load`, and `geometry_inspection`.
8. Confirm CONTACT_MAP and CONNECTIONS rows that support final claims include `evidence_check_ids` pointing to passing validation checks.
9. Confirm sourced standard parts are source-locked and not generated lookalikes.
10. Check that the BOM, validation report, and final engineering report agree on one verdict.

## Visual Review Boundaries

Snapshots, GLB previews, CAD viewer screens, and rendered images are useful for:

- detecting obvious missing bodies;
- checking orientation and gross scale;
- communicating concept/layout state;
- finding labels, collisions, or missing parts for follow-up inspection.

They are not final evidence by themselves. A visual PASS cannot replace command-backed CAD generation, STEP load, geometry inspection, source-lock, BOM, or final report consistency.

## Red-Team Checks

Actively look for:

- metadata-only PASS claims;
- validation hashes that do not match files;
- stale exports after source changes;
- artifact paths outside the milestone with no reason;
- `CONTACT_MAP` or `CONNECTIONS` rows without evidence links;
- source-locked parts missing supplier, SKU, source URL, datasheet, or cached STEP;
- generated standard-part lookalikes marked as final;
- final reports claiming FEA, fatigue, rating, manufacturability, certification, procurement readiness, or physical-test performance without evidence;
- `ENV_BLOCKED` hidden behind successful structure validation.

## Reviewer Output

Write or report a concise reviewer verdict:

```text
Verdict: PASS|BLOCKED
Milestone: milestones/<id>
Commands run:
- ./zen-cad validate --level structure milestones/<id>
- ./zen-cad validate --level completion milestones/<id>

Evidence accepted:
- ...

Findings:
- [P1] ...

Smallest unblock steps:
- ...
```

Prefer file/line references and exact JSON field names over broad criticism.

## Acceptance Rule

Only approve final completion when the Zen CAD completion command passes and the reviewer finds no unsupported final claims. If a useful CAD artifact exists but completion evidence is incomplete, return `BLOCKED` with the artifact paths and smallest unblock steps.
