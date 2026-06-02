# Zen CAD

Zen CAD is a portable, versioned, reproducible agentic mechanical CAD workflow environment.

It is designed to make CAD work consistent, inspectable, and portable across agentic coding/CAD systems such as CoBrA, Claude Code, Cursor, Codex, or similar environments. Zen CAD is not pure text-to-CAD. It packages a source-first/generate-second workflow, milestone structure, artifact templates, validation schemas, review checklists, and reference prompts so a new environment can reproduce the same CAD operating experience.

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
zen-cad-kit/
├─ docs/                  Operating docs for portable use
├─ skills/agentic-cad/    Embedded `/agentic-cad` skill
├─ prompts/               Kickoff, milestone, validation, and release prompts
├─ templates/             Reusable artifact templates
├─ schemas/               JSON schemas for machine-checkable artifacts
├─ checklists/            Intake, sourcing, CAD, assembly, validation, release checks
├─ scripts/               Milestone creation and validation helpers
├─ milestones/_template/  Standard milestone folder skeleton
└─ milestones/001_nema17_belt_linear_actuator/  Reference seed milestone
```

## Quick start

```bash
cd zen-cad-kit
python3 scripts/check_required_files.py .
python3 scripts/check_json_schemas.py .
python3 scripts/validate_milestone.py milestones/001_nema17_belt_linear_actuator
python3 scripts/new_milestone.py --id 002_robot_gripper --title "Robot gripper"
```

## CoBrA usage

Copy or symlink the embedded skill into the CoBrA skills directory if it is not already installed:

```bash
mkdir -p ~/.cobra/workspace/skills/agentic-cad
cp skills/agentic-cad/SKILL.md ~/.cobra/workspace/skills/agentic-cad/SKILL.md
```

Then start a project or milestone with `prompts/project_kickoff.md` or `prompts/new_milestone.md` and require evidence from the validation scripts before declaring completion.

## Non-CoBrA usage

Use `docs/non_cobra_usage.md` and the prompts as plain Markdown operating instructions. Any agentic environment can use Zen CAD if it can read files, edit files, generate or modify CAD artifacts, run validation scripts, and preserve the required evidence.
