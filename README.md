# Zen CAD

Zen CAD is a portable, versioned, reproducible agentic mechanical CAD workflow environment.

It is designed to make CAD work consistent, inspectable, and portable across agentic coding/CAD systems such as CoBrA, Claude Code, Cursor, Codex, or similar environments. Zen CAD is not pure text-to-CAD. It packages a source-first/generate-second workflow, milestone structure, artifact templates, validation schemas, review checklists, setup automation, and reference prompts so a new environment can reproduce the same CAD operating experience.

## Core rules

1. `/agentic-cad` is the top-level workflow and source of truth.
2. Source standard/catalog/off-the-shelf parts before generating geometry.
3. Generate only design-specific custom geometry such as housings, brackets, adapters, links, frames, fixtures, guards, and assembly glue.
4. Generated standard parts are proxies unless sourced and verified.
5. STEP geometry is not engineering certification.
6. Viewer screenshots and GLB previews are human review artifacts, not completion evidence.
7. Completion requires reproducible evidence: CAD source, STEP exports, validation JSON, kernel/export checks, CONTACT_MAP, CONNECTIONS, BOM, and final engineering report.
8. New CAD jobs are milestones by default.
9. Workflow improvements should be fed back into `/agentic-cad`.

## Repository layout

```text
zen-cad/
├─ docs/                  Operating docs for portable use
├─ skills/                Embedded `/agentic-cad`, `/spec-to-cad`, and verifier skills
├─ prompts/               Kickoff, milestone, validation, and release prompts
├─ templates/             Reusable artifact templates
├─ schemas/               JSON schemas for machine-checkable artifacts
├─ checklists/            Intake, sourcing, CAD, assembly, validation, release checks
├─ scripts/               One-command setup, milestone, and validation helpers
├─ milestones/_template/  Standard milestone folder skeleton
└─ milestones/001_nema17_belt_linear_actuator/  Reference seed milestone
```

## Quick start: one-command setup

From the cloned repo root, run the setup helper first:

```bash
python3 scripts/setup_zen_cad.py
```

For CoBrA, sync the embedded `/agentic-cad`, `/spec-to-cad`, and `/self-evolving-producer-verifier` skills and run validation in one command:

```bash
python3 scripts/setup_zen_cad.py --sync-cobra-skill
```

## Prompt-first milestone startup

After setup, the user-facing CoBrA flow is natural language, not another Python command. In a new CoBrA session or prompt window, the user can simply say the CAD goal, for example:

```text
기어 박스를 만들고 싶어
```

The agent must treat that as a new Zen CAD job request. Do not ask the user to run a milestone command or manually choose the milestone id/title. Instead, the agent internally runs this from the Zen CAD repository root:

```bash
python3 scripts/new_milestone.py --request "<goal>"
```

For `기어 박스를 만들고 싶어`, that creates the next available milestone such as `002_gearbox` with title `Gearbox`, then the agent continues with `prompts/new_milestone.md` and `skills/agentic-cad/SKILL.md`.

The setup-time `--milestone-request` path is still available for automation, smoke tests, or non-interactive agents:

```bash
python3 scripts/setup_zen_cad.py \
  --milestone-request "foldable drone landing gear를 만들고 싶어"
```

The explicit path also still works when you need to pin a specific id/title:

```bash
python3 scripts/setup_zen_cad.py \
  --milestone-id 002_desktop_cnc_fixture \
  --milestone-title "Desktop CNC workholding fixture"
```

Good natural-language starting topics include gearbox, robot arm joint, watch escapement, drone frame, camera mount, enclosure, fixture, actuator, or any other mechanical CAD job.

## Manual validation commands

The setup helper runs these checks for you, but they can also be run manually. Required-file and schema checks cover every milestone folder under `milestones/`.

```bash
python3 scripts/check_required_files.py .
python3 scripts/check_json_schemas.py .
python3 scripts/validate_milestone.py milestones/001_nema17_belt_linear_actuator
python3 scripts/validate_milestone.py milestones/_template
```

## CoBrA usage

Use `docs/cobra_usage.md` for the full CoBrA flow. The short version is:

```bash
python3 scripts/setup_zen_cad.py --sync-cobra-skill
```

Then start a project or milestone with `prompts/project_kickoff.md` or say the CAD goal naturally, e.g. `기어 박스를 만들고 싶어`; the agent should use `prompts/new_milestone.md`, internally run `python3 scripts/new_milestone.py --request "<goal>"`, and activate the created milestone before editing artifacts. Require evidence from the validation scripts before declaring completion.

## Non-CoBrA usage

Use `docs/non_cobra_usage.md` and the prompts as plain Markdown operating instructions. Any agentic environment can use Zen CAD if it can read files, edit files, generate or modify CAD artifacts, run validation scripts, and preserve the required evidence.
