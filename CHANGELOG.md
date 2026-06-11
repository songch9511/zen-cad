# Changelog

## Unreleased

## 1.1.0 - 2026-06-11

- Add `cad-replacement` guidance for replacing layout proxies with source-locked STEP/STP or detail CAD while preserving interface frames, datums, axes, bolt patterns, clearances, and locked layout facts.
- Add `constrained-detail-cad` guidance for generating custom detail CAD from locked facts plus user shape intent, protected zones, manufacturing assumptions, and post-generation inspection.
- Add contract schemas for `interface_frame`, `replacement_plan`, and `detail_shape_plan` artifacts so agents can express replacement and custom generation work without relying on prose-only instructions.
- Update the plugin and documentation to position layout proxies as precise interface scaffolds for source replacement and constrained detail generation, not merely rough visual placeholders.

## 1.0.2 - 2026-06-11

- Add visual inspection and repair guidance for generated CAD review, including floating bodies, interference, clearance, fastening, alignment, mesh/contact, and support-path checks.
- Update `cad-spec` and `cad-handoff` workflows so agents ask for a Subagent Dispatch Plan when subagents are available, while using an explicit sequential fallback when they are not.
- Keep subagent orchestration as skill guidance only; do not add runtime/tool exposure that physically forces subagent spawning.
- Clean up the README around scope, usage, command flow, benchmarks, and the visual review boundary.

## 1.0.1 - 2026-06-10

- Add `tools/generate_cad_artifact.py` to execute generated build123d source, export a primary STEP artifact, re-import it, and record export/import/bbox/volume checks.
- Extend the contract pipeline so `--target-harness build123d` produces a generated STEP artifact and CAD generation inspection report before proceed review.
- Update docs and skills so Zen CAD is no longer framed as contract-only when a local build123d generation path is available.
- Add feature-plan carry-through for holes, bores, bolt-circle/repeated patterns, rectangular top chamfers, simplified gear teeth, and supported cylinder edge-round approximations.
- Add native benchmark contract packages for a rectangular calibration block, circular flange, and simplified planetary gear stage.
- Add `tools/package_viewer_link.py` and runner integration so generated STEP artifacts can enter proceed review with a local CAD Viewer link.
- Add `tools/capture_viewer_snapshot.py` and runner `--capture-viewer-snapshot` support so proceed gates can include PNG viewer evidence.
- Add `tools/download_step_part.py` for `api.step.parts` search/download, sha256 verification, and checksum-backed source-lock evidence.
- Tighten source-lock validation so checksum-recorded STEP/STP evidence requires a 64-hex sha256, and prefer local verified STEP copies over remote STEP URLs during source export.

## 1.0.0

- Add a dependency-free CAD Viewer review brief packager that turns proceed-gate and optional pipeline/viewer artifacts into a downstream review handoff.
- Make the viewer handoff explicit that screenshots, snapshots, and viewer links are review aids, not completion evidence.
- Add runner-backed tests for the viewer review brief and document the command flow.
- Add a CAD Skills/text-to-cad prompt bundle packager that accepts approved detail handoffs without generating CAD itself.
- Add machine-readable `source_lock_evidence` for final-stage standard/catalog part source evidence while keeping layout interface signatures layout-only.
- Add a dependency-free `tools/generate_source_lock_evidence.py` generator for explicit step.parts, manufacturer, datasheet, project-file, and user-provided source locators without catalog crawling.
- Add source-lock validation rules that prevent layout-only evidence from becoming a source lock and keep rating/certification claims out of the artifact.
- Import source-locked STEP/STP geometry into generated build123d source and replace matching layout proxy primitives when geometry references are present.
- Document the source-lock boundary in the interface signature references.
- Keep contract documents on `schema_version: 0.8.0` for contract compatibility.

## 0.9.0

- Bump the product and core skill versions to 0.9.0.
- Add the 0.9.0 one-command kernel-neutral contract pipeline runner for validation, layout proxy generation, scene inspection, CAD source export, source inspection, and proceed packaging.
- Add explicit proceed approval artifacts before detail handoff generation.
- Document runner-first usage across README and generic usage docs while keeping the phase tools available for focused diagnosis.
- Keep contract documents on `schema_version: 0.8.0` for contract compatibility.

## 0.8.9

- Reset Zen CAD to a focused CAD-native skill pack.
- Keep only the spec-first skills: `/cad-spec`, `/assembly-layout`, `/interface-signatures`, and `/cad-handoff`.
- Add specialist subagent orchestration guidance to `/cad-spec`.
- Add parameter contract, export target, inspection, and repair-loop guidance inspired by text-to-cad workflows.
- Add machine-readable schema foundation for CAD specs, layout contracts, interface signatures, inspection reports, and handoff packets.
- Add a small layout-ready interface registry for common motors, belts, bearings, fasteners, shaft/bores, and rails.
- Add `tools/validate_contract.py` for dependency-free schema, registry, and contract-package validation.
- Add `tools/generate_layout_proxy.py` for dependency-free kernel-neutral layout proxy scene generation.
- Add `tools/inspect_layout_proxy.py` for dependency-free locked-facts inspection of layout proxy scenes.
- Add `tools/export_cad_source.py`, `tools/inspect_cad_source.py`, `tools/package_proceed_gate.py`, and `tools/generate_detail_handoff.py` to complete the 0.8.9 kernel-neutral handoff pipeline.
- Remove old workflow skills, workspace-specific CLI helpers, templates, checklists, prompts, plugins, fixtures, and release-package machinery from the main surface.
