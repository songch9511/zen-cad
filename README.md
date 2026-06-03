# Zen CAD

<div align="center">

<pre>
███████╗███████╗███╗   ██╗      ██████╗ █████╗ ██████╗
╚══███╔╝██╔════╝████╗  ██║     ██╔════╝██╔══██╗██╔══██╗
  ███╔╝ █████╗  ██╔██╗ ██║     ██║     ███████║██║  ██║
 ███╔╝  ██╔══╝  ██║╚██╗██║     ██║     ██╔══██║██║  ██║
███████╗███████╗██║ ╚████║     ╚██████╗██║  ██║██████╔╝
╚══════╝╚══════╝╚═╝  ╚═══╝      ╚═════╝╚═╝  ╚═╝╚═════╝
</pre>

Harness-native CAD workflow for source-aware mechanical design agents

[![Version](https://img.shields.io/badge/version-0.6.2-4A5568?style=for-the-badge)](VERSION)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](docs/environment_setup.md)
[![STEP](https://img.shields.io/badge/STEP-first-00A676?style=for-the-badge)](skills/spec-to-cad/SKILL.md)
[![CoBrA](https://img.shields.io/badge/CoBrA-adapter-2F80ED?style=for-the-badge)](plugins/cobra/README.md)
[![Codex](https://img.shields.io/badge/Codex-adapter-000000?style=for-the-badge)](plugins/codex/README.md)
[![Claude_Code](https://img.shields.io/badge/Claude_Code-adapter-6B46C1?style=for-the-badge)](plugins/claude-code/README.md)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

</div>

## Overview

Zen CAD is a portable CAD harness for agentic mechanical design. It is not a CAD kernel, STEP part search engine, or one-shot text-to-CAD model. It gives CoBrA, Codex, Claude Code, Cursor, and similar agents a shared operating contract for turning natural-language mechanical goals into milestone-scoped CAD artifacts with sourcing records, validation evidence, BOMs, blockers, and final engineering reports.

The default 0.6.x model is **generate first, gate later**:

1. Start from a natural-language CAD goal.
2. Create a milestone workspace automatically.
3. Let the harness use its available CAD tools to produce concept/layout CAD.
4. Source standard/catalog parts before final claims.
5. Generate only design-specific custom CAD as final geometry.
6. Validate final/release claims with reproducible evidence gates.

Zen CAD is designed to wrap a STEP-first CAD runner. When [earthtojake/text-to-cad](https://github.com/earthtojake/text-to-cad) or an equivalent CAD skill is available, use it as the preferred generation, inspection, and snapshot path. Zen CAD provides the surrounding milestone, source-lock, evidence, BOM, report, and release contract.

## Skills

| Skill | Summary | Source |
| --- | --- | --- |
| Agentic CAD | Top-level sourcing-aware orchestrator for requirements, research, part classification, CAD handoff, validation, BOM, and reporting. | [skills/agentic-cad](skills/agentic-cad/SKILL.md) |
| Spec-to-CAD | Downstream CAD execution skill for measurable specs, STEP/STL exports, CONTACT_MAP/CONNECTIONS, and kernel-backed evidence. | [skills/spec-to-cad](skills/spec-to-cad/SKILL.md) |
| Self-Evolving Producer Verifier | Producer/verifier workflow for independent review, failure-driven iteration, and workflow feedback. | [skills/self-evolving-producer-verifier](skills/self-evolving-producer-verifier/SKILL.md) |

## Harness Adapters

| Harness | Adapter | How Zen CAD is applied |
| --- | --- | --- |
| CoBrA | [plugins/cobra](plugins/cobra/README.md) | `./zen-cad init --with-cobra` installs bundled skills and writes `ZEN_CAD_WORKSPACE.md` beside each installed skill. |
| Codex | [plugins/codex](plugins/codex/README.md) | Open this repository as the workspace. Use Codex file edits, terminal execution, and installed CAD skills such as text-to-cad. |
| Claude Code | [plugins/claude-code](plugins/claude-code/README.md) | Open this repository as the project. Keep the active milestone and validation commands explicit. |

See [docs/harness_adapters.md](docs/harness_adapters.md) for the shared adapter contract.

## Quickstart

Clone the repository and run the first-run check:

```bash
git clone https://github.com/songch9511/zen-cad.git
cd zen-cad
./zen-cad doctor
```

For CoBrA, install the bundled skills:

```bash
./zen-cad init --with-cobra
```

For Codex or Claude Code, open this repository as the workspace/project root.

Then ask the agent for CAD in natural language:

```text
기어 박스를 만들고 싶어
```

The agent should treat that as a prompt-first milestone start and internally run:

```bash
python3 scripts/new_milestone.py --request "<goal>"
```

Manual terminal fallback:

```bash
./zen-cad new --maturity concept "기어 박스를 만들고 싶어"
```

## Milestone Workflow

Each CAD job lives under `milestones/<id>/`:

```text
milestones/003_gearbox/
├─ 00_requirements/requirements_brief.md
├─ 01_research/research_log.md
├─ 02_parts/part_classification_table.md
├─ 02_parts/selected_parts_manifest.json
├─ 03_cad/custom_cad_handoff.yaml
├─ 04_assembly/contact_map.json
├─ 04_assembly/connections.json
├─ 05_validation/validation_report.json
├─ 06_bom/bom.csv
└─ 07_report/final_engineering_report.md
```

The milestone folder is the durable source of truth for requirements, research, sourced parts, CAD handoff, assembly contract, validation evidence, BOM, blockers, and final report.

## Validation

Structure validation checks required files, schemas, BOM headers, and milestone skeletons:

```bash
./zen-cad validate --level structure milestones/<id>
```

Completion validation checks final evidence gates:

```bash
./zen-cad validate --level completion milestones/<id>
```

Equivalent explicit commands:

```bash
./zen-cad validate-structure milestones/<id>
./zen-cad validate-completion milestones/<id>
./zen-cad source-lock milestones/<id>
./zen-cad blocked-report --write milestones/<id>
```

The two results are intentionally separate:

- `Zen CAD validation result: PASS` means the repository and milestone structure are valid.
- `Zen CAD completion validation result: PASS` means source-lock, CAD exports, assembly contract, command-backed CAD evidence, BOM, and final report gates are complete.
- `BLOCKED` is a valid truthful result for concept/layout milestones.

## Evidence Contract

Final completion requires reproducible evidence. These do not count as final evidence by themselves:

- screenshots
- GLB or viewer previews
- worker summaries
- proxy/envelope geometry
- metadata-only PASS claims

A final milestone should include:

- CAD source
- STEP/STL exports
- source-lock records for standard/catalog parts
- CONTACT_MAP and CONNECTIONS
- kernel/export/loadability checks
- validation JSON with command metadata, result status, evidence type, artifact paths, file sizes, and SHA-256 hashes
- at least `cad_generation`, `step_load`, and `geometry_inspection` evidence types for completion PASS
- local `doctor --cad-required` success, or command-backed `environment` evidence from the CAD runtime that generated the final artifacts
- BOM
- final engineering report

Zen CAD separates CAD validation from engineering certification. STEP geometry does not prove structural safety, rating, material, fatigue life, manufacturability, compliance, or certification unless the relevant analysis was actually performed.

## Included Demo

The repository includes a small final demo milestone:

```bash
./zen-cad validate-completion milestones/002_nema17_mount_plate
```

The demo is intentionally small, but its PASS is hash-backed: the validation report records command metadata and matching artifact hashes for CAD source, STEP/STL exports, geometry inspection JSON, CONTACT_MAP/CONNECTIONS, BOM, and final report.

The original reference milestone remains intentionally blocked until standard parts, generated CAD, STEP cache, and final validation evidence are completed:

```bash
./zen-cad validate-completion milestones/001_nema17_belt_linear_actuator
```

## Repository Layout

```text
zen-cad/
├─ docs/                  Operating docs and harness adapter contract
├─ plugins/               CoBrA, Codex, and Claude Code adapter notes
├─ skills/                Portable CAD workflow skills
├─ prompts/               Kickoff, milestone, validation, and release prompts
├─ templates/             Reusable milestone artifact templates
├─ schemas/               Machine-checkable JSON and CSV schemas
├─ checklists/            Intake, sourcing, CAD, assembly, validation, release
├─ packages/              Validation-core packaging contract
├─ scripts/               Setup, milestone, validation, and release helpers
├─ milestones/_template/  Standard milestone skeleton
└─ zen-cad                Repo-local CLI wrapper
```

## Development Checks

Run the local test suite:

```bash
python3 -m unittest discover -s tests
```

Run repository validation:

```bash
./zen-cad doctor
./zen-cad validate
```

For final/release-grade claims, require CAD tooling:

```bash
./zen-cad doctor --cad-required
```

## Current Boundary

Zen CAD does not ship a full CAD kernel, STEP part search engine, or browser viewer. It expects the harness to supply those capabilities directly or through installed tools such as text-to-cad, build123d, CadQuery, FreeCAD, OpenSCAD, or a project-approved CAD stack. Zen CAD's job is to make that work milestone-scoped, source-aware, reproducible, and honest about completion.
