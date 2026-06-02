# Changelog

## Unreleased

## 0.4.0

- Add CAD toolchain preflight to `zen-cad doctor`, including Python/venv, numpy, trimesh, CadQuery/OpenSCAD, artifact/cache write access, and `--cad-required` ENV_BLOCKED behavior.
- Split validation into structure and completion levels with `validate --level structure|completion`, `validate-structure`, and `validate-completion`.
- Add completion gate analysis for Gate 0 through Gate 7 so source-lock, proxy-only artifacts, STEP cache/export evidence, CAD-kernel validation, BOM, and final report status cannot be conflated with structure PASS.
- Add `zen-cad source-lock` to audit standard/catalog parts before CAD generation and block proxy-only or incomplete standard-part records from completion evidence.
- Add `zen-cad blocked-report --write` to produce a truthful PASS/BLOCKED evidence report with completed gates, blocking gates, and the smallest unblock step.
- Extend selected-parts and validation-report templates/schemas with 0.4.0 source-lock and gate evidence fields.
- Update `/agentic-cad`, `/spec-to-cad`, README, docs, and checklists around evidence-gated workflow, truthful BLOCKED reports, and proxy isolation.

- Add a repo-local `./zen-cad` first-run CLI with `doctor`, `init`, `new`, and `validate` commands.
- Clarify that CoBrA skill sync installs workflow skills but does not bind the active workspace to the Zen CAD repository.
- Add human-readable PASS/BLOCKED summaries for first-run validation and completion evidence state.
- Strengthen required-file and schema validation across every milestone directory.
- Remove committed release snapshots and generated smoke milestones from the source tree.
- Bundle `/spec-to-cad` and `/self-evolving-producer-verifier` companion skills required by `/agentic-cad`.

## 0.3.0

- Initial portable Zen CAD repo/template kit.
- Embeds the current `/agentic-cad` source-of-truth skill.
- Adds milestone templates, artifact schemas, checklists, prompts, and validation scripts.
- Seeds a reference NEMA17 belt-driven linear actuator milestone.
