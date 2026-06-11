# Zen CAD Viewer Review Brief

- Spec ID: `compact_belt_drive_module`
- Proceed gate: `work/compact_belt_drive_module/review/proceed_gate.json`
- Gate status: `ready_for_user_review`
- Reviewer role: `cad-viewer`
- Pipeline run: `work/compact_belt_drive_module/review/pipeline_run.json`
- Pipeline status: `ready_for_user_review`
- Target harness: `unknown`

## Review Objective

Open the layout/proceed artifacts in a CAD viewer and review visible positioning, interface orientation, assembly structure, and obvious drift against the locked layout facts.

Screenshots, viewer links, and visual snapshots are review aids only. Do not mark the package complete from screenshots alone; use the proceed gate status, check summary, inspection reports, and downstream geometry measurements as completion evidence.

## Source Package

- `layout_proxy_scene`: `work/compact_belt_drive_module/review/layout/layout_proxy.scene.json`
- `source`: `work/compact_belt_drive_module/review/source/layout_proxy_build123d.py`

## Inspection Reports

- `work/compact_belt_drive_module/review/layout/locked_facts.inspection_report.json`: status `partial`, proceed `ready_for_layout_generation`
- `work/compact_belt_drive_module/review/source/source.inspection_report.json`: status `partial`, proceed `ready_for_proceed_review`

## Viewer Artifacts

- `step`: `work/compact_belt_drive_module/review/step/compact_belt_drive_module_layout.step`
- `py`: `work/compact_belt_drive_module/review/source/compact_belt_drive_module_cadquery.py`
- `viewer_data`: `work/compact_belt_drive_module/review/source/cad_source_manifest.json`

## Locked Layout Facts

- `root_frame_locked`
- `shaft_axes_parallel_z_locked`
- `pulley_center_distance_locked`
- `motor_axis_position_locked`
- `output_axis_position_locked`
- `belt_midplane_locked`
- `motor_mount_pattern_locked`
- `bearing_interface_locked`
- `output_shaft_interface_locked`
- `gt2_interface_locked`
- `fastener_clearance_locked`

## Check Summary

- Passed: `34`
- Partial: `2`
- Failed: `0`
- Skipped: `10`

## Known Limitations

- `Downstream CAD geometry checks are still required before proceed review.`
- `Inspection covers kernel-neutral scene contract only.`
- `Inspection verifies source-level carry-through, not generated STEP geometry.`
- `Run downstream CAD generation and geometry inspection before final proceed approval.`
- `Scene carries skipped geometry checks that require a CAD harness.`

## CAD Viewer Tasks

1. Open the listed layout and source artifacts that the viewer supports.
2. Compare visible axes, frames, part relationships, interface datums, clearances, and motion cues against the locked facts.
3. Cross-check any visual finding against the inspection reports before calling it passed.
4. If a visual concern is not covered by a check, request a distance, axis, frame, mate, or geometry measurement instead of approving by sight.
5. Record skipped viewer steps with the missing tool, unsupported artifact, or unavailable measurement.

## Decision Guidance

- Available proceed gate decisions: `proceed, revise_layout, detail_upgrade`.
- The viewer may recommend proceed only if visible review finds no drift and inspection evidence still supports the locked facts.
- Detail CAD handoff still requires an explicit proceed approval artifact.
- Final CAD readiness requires downstream geometry checks beyond this viewer brief.

## Review Notes Template

```text
viewer_artifacts_opened:
visible_findings:
measurement_requests:
blockers:
recommended_decision:
```
