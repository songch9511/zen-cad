# Changelog

## 0.8.0

- Reset Zen CAD to a focused CAD-native skill pack.
- Keep only the spec-first skills: `/cad-spec`, `/assembly-layout`, `/interface-signatures`, and `/cad-handoff`.
- Add specialist subagent orchestration guidance to `/cad-spec`.
- Add parameter contract, export target, inspection, and repair-loop guidance inspired by text-to-cad workflows.
- Add machine-readable schema foundation for CAD specs, layout contracts, interface signatures, inspection reports, and handoff packets.
- Add a small layout-ready interface registry for common motors, belts, bearings, fasteners, shaft/bores, and rails.
- Add `tools/validate_contract.py` for dependency-free schema, registry, and contract-package validation.
- Add `tools/generate_layout_proxy.py` for dependency-free kernel-neutral layout proxy scene generation.
- Remove old workflow skills, workspace-specific CLI helpers, templates, checklists, prompts, plugins, fixtures, and release-package machinery from the main surface.
