# Changelog

## Unreleased

## 0.6.6

- Tighten `/agentic-cad` startup semantics so prompt-first milestone creation depends on a resolved Zen CAD workspace root, not CoBrA daemon/session cwd.
- Document equivalent milestone creation commands using explicit command cwd or `--root`.
- Add regression coverage against ambiguous "running inside a Zen CAD repository" and "from the Zen CAD repository root" wording in the CoBrA startup contract.

## 0.6.5

- Clarify the CoBrA adapter boundary: the Zen CAD repository is not the CoBrA daemon cwd.
- Update `doctor`, `init --with-cobra`, and CoBrA docs to use `ZEN_CAD_WORKSPACE.md` plus explicit command cwd/`--root` for Zen CAD work.
- Add regression coverage so stale "Start CoBrA from this repo" guidance cannot return.

## 0.6.4

- Add focused companion skills inspired by the text-to-cad skill split: `/source-step-parts`, `/cad-artifact-reviewer`, `/manufacturing-preflight`, and `/mechanism-kinematics`.
- Route `/agentic-cad` to the new companion skills for source-locking, artifact review, manufacturing preflight, and kinematic contracts.
- Extend CoBrA sync, doctor freshness checks, required-file validation, and regression tests to cover all bundled Zen CAD skills.
- Update README and adapter docs to describe the expanded skill pack without turning Zen CAD into a CAD kernel or manufacturing certification tool.

## 0.6.3

- Rewrite `/spec-to-cad` as a Zen CAD milestone-first, text-to-cad-first execution skill with canonical artifact paths.
- Remove stale GFL/PM160/private-path assumptions from the shipped CAD execution skill.
- Align `/agentic-cad` required artifacts, Gate 0 environment evidence, and validation report examples with the 0.6.x completion gates.
- Add portable fallback guidance to `/self-evolving-producer-verifier` for harnesses without CoBrA loop primitives.
- Add skill contract regression tests for text-to-cad guidance, canonical milestone paths, portable producer-verifier fallback, and skill versions.

## 0.6.2

- Rewrite README in an official distribution style with skill/adaptor tables, quickstart, validation gates, and evidence contract.
- Add explicit earthtojake/text-to-cad compatibility guidance to the harness adapter docs.
- Strengthen completion validation so PASS reports must include command metadata, evidence types, artifact paths, file sizes, and SHA-256 hashes.
- Require final completion reports to include `cad_generation`, `step_load`, and `geometry_inspection` evidence types.
- Require `environment` evidence when local final CAD preflight is blocked but a committed final artifact is still being claimed.
- Tie CONTACT_MAP and CONNECTIONS rows to passing geometry evidence through `evidence_check_ids`.
- Upgrade the `002_nema17_mount_plate` demo to a 0.6.2 hash-backed PASS fixture and add red-team regression tests for fake PASS reports.

## 0.6.1

- Fix the CoBrA adapter boundary: `init --with-cobra` now installs a `ZEN_CAD_WORKSPACE.md` binding beside each synced skill so installed CoBrA skills can recover the Zen CAD repo root.
- Split CoBrA skill discovery/workspace-binding diagnostics from local CAD `ENV_BLOCKED` diagnostics in `zen-cad doctor`.
- Teach `/agentic-cad` and `/spec-to-cad` to read the CoBrA workspace binding when they are invoked from an installed skill directory instead of the Zen CAD repo root.
- Clarify that missing CAD packages block final/release evidence gates, while missing or unbound CoBrA skills block harness discovery.

## 0.6.0

- Reposition Zen CAD as a harness-native, generate-first CAD skill pack: portable workflow skills plus a lightweight optional validation CLI and thin harness adapters.
- Add `docs/harness_adapters.md` and `plugins/` adapter notes for CoBrA, Codex-style, and Claude Code-style agent harnesses.
- Add `packages/zen_cad_core/` as the documented validation-core boundary while keeping the existing repo-local CLI and scripts stable.
- Update README and usage docs around the harness/skills/core responsibility split: harnesses provide CAD generation/execution, Zen CAD provides lightweight workflow policy and optional final completion gates.
- Include adapter/core documentation and the completion-PASS demo milestone in release package exports and required-file checks.

## 0.5.0

- Shift Zen CAD to a generation-first workflow: concept/layout milestones may use proxy or envelope CAD while final completion remains evidence-gated.
- Add `concept`, `layout`, and `final` milestone maturity modes across milestone creation, validation, source-lock severity, templates, and schemas.
- Promote build123d plus OCP to the preferred CAD/export backend in `zen-cad doctor`, with `--python` and `ZEN_CAD_PYTHON` support for CoBrA worker/runtime alignment.
- Add CoBrA skill freshness checks that compare installed skill files against the repository source and warn when stale skills are in use.
- Add a final, completion-PASS `002_nema17_mount_plate` demo milestone with build123d source, STEP/STL exports, OCP load evidence, BOM, and final report.
- Fix milestone template placeholder replacement for all text artifacts created by `scripts/new_milestone.py`.

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
