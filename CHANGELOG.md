# Changelog

## Unreleased

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
