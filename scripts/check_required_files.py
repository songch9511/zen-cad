#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT_REQUIRED = [
    'README.md', 'VERSION', 'CHANGELOG.md',
    'docs/philosophy.md', 'docs/operating_principles.md', 'docs/source_first_generate_second.md', 'docs/completion_evidence.md', 'docs/milestone_protocol.md', 'docs/environment_setup.md', 'docs/generic_usage.md', 'docs/harness_adapters.md',
    'skills/cad-spec/SKILL.md', 'skills/cad-spec/agents/openai.yaml', 'skills/cad-spec/references/natural-language-to-cad-spec.md', 'skills/cad-spec/references/assembly-positioning.md', 'skills/cad-spec/references/interface-primitives.md', 'skills/cad-spec/references/motion-and-drivetrain.md', 'skills/cad-spec/references/proxy-fidelity.md', 'skills/cad-spec/references/proceed-gate.md', 'skills/cad-spec/references/downstream-cad-handoff.md',
    'skills/assembly-layout/SKILL.md', 'skills/assembly-layout/references/layout-contract.md', 'skills/assembly-layout/references/review-checklist.md',
    'skills/interface-signatures/SKILL.md', 'skills/interface-signatures/references/common-families.md', 'skills/interface-signatures/references/signature-quality.md',
    'skills/cad-handoff/SKILL.md', 'skills/cad-handoff/references/harness-briefs.md',
    'skills/agentic-cad/SKILL.md', 'skills/cad-artifact-reviewer/SKILL.md', 'skills/manufacturing-preflight/SKILL.md', 'skills/mechanism-kinematics/SKILL.md', 'skills/spec-to-cad/SKILL.md', 'skills/self-evolving-producer-verifier/SKILL.md', 'skills/source-step-parts/SKILL.md',
    'plugins/README.md', 'plugins/codex/README.md', 'plugins/claude-code/README.md',
    'packages/zen_cad_core/README.md',
    'prompts/project_kickoff.md', 'prompts/new_milestone.md', 'prompts/validation_review.md', 'prompts/release_review.md', 'prompts/feedback_to_agentic_cad_skill.md',
    'templates/PROJECT_MANIFEST.yaml', 'templates/milestone.yaml', 'templates/requirements_brief.md', 'templates/part_classification_table.md', 'templates/selected_parts_manifest.json', 'templates/custom_cad_handoff.yaml', 'templates/contact_map.json', 'templates/connections.json', 'templates/validation_report.json', 'templates/bom.csv', 'templates/final_engineering_report.md',
    'schemas/selected_parts_manifest.schema.json', 'schemas/contact_map.schema.json', 'schemas/connections.schema.json', 'schemas/validation_report.schema.json', 'schemas/bom.schema.json', 'schemas/bom.columns.json',
    'checklists/intake_checklist.md', 'checklists/sourcing_checklist.md', 'checklists/custom_cad_checklist.md', 'checklists/assembly_checklist.md', 'checklists/validation_checklist.md', 'checklists/release_checklist.md',
    'zen-cad',
    'scripts/setup_zen_cad.py', 'scripts/zen_cad.py', 'scripts/new_milestone.py', 'scripts/validate_milestone.py', 'scripts/check_json_schemas.py', 'scripts/check_required_files.py', 'scripts/export_release_package.py',
    'milestones/_template/milestone.yaml',
    'milestones/001_nema17_belt_linear_actuator/milestone.yaml',
]

MILESTONE_REQUIRED = [
    'milestone.yaml',
    '00_requirements/requirements_brief.md',
    '01_research/research_log.md',
    '02_parts/part_classification_table.md',
    '02_parts/selected_parts_manifest.json',
    '03_cad/custom_cad_handoff.yaml',
    '04_assembly/contact_map.json',
    '04_assembly/connections.json',
    '05_validation/validation_report.json',
    '06_bom/bom.csv',
    '07_report/final_engineering_report.md',
]


def iter_milestone_dirs(root: Path) -> list[Path]:
    milestones_dir = root / 'milestones'
    if not milestones_dir.exists():
        return []
    return sorted(
        (child for child in milestones_dir.iterdir() if child.is_dir() and (child / 'milestone.yaml').exists()),
        key=lambda path: path.name,
    )


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    missing = [p for p in ROOT_REQUIRED if not (root / p).exists()]
    milestone_dirs = iter_milestone_dirs(root)
    for milestone in milestone_dirs:
        for rel in MILESTONE_REQUIRED:
            path = milestone / rel
            if not path.exists():
                missing.append(str(path.relative_to(root)))
    if missing:
        print('Missing required files:')
        for path in missing:
            print(f'- {path}')
        return 1
    print(f'OK: {len(ROOT_REQUIRED)} root files and {len(milestone_dirs)} milestone skeletons present under {root}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
