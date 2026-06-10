# Changelog

## 1.0.0

- Add a dependency-free CAD Viewer review brief packager that turns proceed-gate and optional pipeline/viewer artifacts into a downstream review handoff.
- Make the viewer handoff explicit that screenshots, snapshots, and viewer links are review aids, not completion evidence.
- Add runner-backed tests for the viewer review brief and document the command flow.
- Add a CAD Skills/text-to-cad prompt bundle packager that accepts approved detail handoffs without generating CAD itself.
- Add machine-readable `source_lock_evidence` for final-stage standard/catalog part source evidence while keeping layout interface signatures layout-only.
- Add a dependency-free `tools/generate_source_lock_evidence.py` generator for explicit step.parts, manufacturer, datasheet, project-file, and user-provided source locators without catalog crawling.
- Add source-lock validation rules that prevent layout-only evidence from becoming a source lock and keep rating/certification claims out of the artifact.
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
