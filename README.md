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
├─ skills/agentic-cad/    Embedded `/agentic-cad` skill
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

For CoBrA, sync the embedded `/agentic-cad` skill and run validation in one command:

```bash
python3 scripts/setup_zen_cad.py --sync-cobra-skill
```

To sync CoBrA, create a first milestone, and validate everything in one command:

```bash
python3 scripts/setup_zen_cad.py \
  --sync-cobra-skill \
  --milestone-id 002_robot_gripper \
  --milestone-title "Small servo-driven robot gripper"
```

For Claude Code, Codex, Cursor, or other non-CoBrA agents, open this repository as the project root and run:

```bash
python3 scripts/setup_zen_cad.py \
  --milestone-id 002_robot_gripper \
  --milestone-title "Small servo-driven robot gripper"
```

Then ask the agent to read `skills/agentic-cad/SKILL.md` and `prompts/new_milestone.md` before editing the milestone artifacts.

## Manual validation commands

The setup helper runs these checks for you, but they can also be run manually:

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

Then start a project or milestone with `prompts/project_kickoff.md` or `prompts/new_milestone.md` and require evidence from the validation scripts before declaring completion.

## Non-CoBrA usage

Use `docs/non_cobra_usage.md` and the prompts as plain Markdown operating instructions. Any agentic environment can use Zen CAD if it can read files, edit files, generate or modify CAD artifacts, run validation scripts, and preserve the required evidence.
