#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

REQUIRED = [
    'README.md', 'VERSION', 'CHANGELOG.md',
    'docs/philosophy.md', 'docs/operating_principles.md', 'docs/source_first_generate_second.md', 'docs/completion_evidence.md', 'docs/milestone_protocol.md', 'docs/environment_setup.md', 'docs/cobra_usage.md', 'docs/non_cobra_usage.md',
    'skills/agentic-cad/SKILL.md',
    'prompts/project_kickoff.md', 'prompts/new_milestone.md', 'prompts/validation_review.md', 'prompts/release_review.md', 'prompts/feedback_to_agentic_cad_skill.md',
    'templates/PROJECT_MANIFEST.yaml', 'templates/milestone.yaml', 'templates/requirements_brief.md', 'templates/part_classification_table.md', 'templates/selected_parts_manifest.json', 'templates/custom_cad_handoff.yaml', 'templates/contact_map.json', 'templates/connections.json', 'templates/validation_report.json', 'templates/bom.csv', 'templates/final_engineering_report.md',
    'schemas/selected_parts_manifest.schema.json', 'schemas/contact_map.schema.json', 'schemas/connections.schema.json', 'schemas/validation_report.schema.json', 'schemas/bom.schema.json', 'schemas/bom.columns.json',
    'checklists/intake_checklist.md', 'checklists/sourcing_checklist.md', 'checklists/custom_cad_checklist.md', 'checklists/assembly_checklist.md', 'checklists/validation_checklist.md', 'checklists/release_checklist.md',
    'scripts/new_milestone.py', 'scripts/validate_milestone.py', 'scripts/check_json_schemas.py', 'scripts/check_required_files.py', 'scripts/export_release_package.py',
    'milestones/_template/milestone.yaml',
    'milestones/_template/00_requirements/requirements_brief.md',
    'milestones/_template/02_parts/selected_parts_manifest.json',
    'milestones/_template/04_assembly/contact_map.json',
    'milestones/_template/04_assembly/connections.json',
    'milestones/_template/05_validation/validation_report.json',
    'milestones/_template/06_bom/bom.csv',
    'milestones/_template/07_report/final_engineering_report.md',
    'milestones/001_nema17_belt_linear_actuator/milestone.yaml',
    'milestones/001_nema17_belt_linear_actuator/00_requirements/requirements_brief.md',
    'milestones/001_nema17_belt_linear_actuator/02_parts/selected_parts_manifest.json',
    'milestones/001_nema17_belt_linear_actuator/04_assembly/contact_map.json',
    'milestones/001_nema17_belt_linear_actuator/04_assembly/connections.json',
    'milestones/001_nema17_belt_linear_actuator/05_validation/validation_report.json',
    'milestones/001_nema17_belt_linear_actuator/06_bom/bom.csv',
    'milestones/001_nema17_belt_linear_actuator/07_report/final_engineering_report.md',
]

def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    missing = [p for p in REQUIRED if not (root / p).exists()]
    if missing:
        print('Missing required files:')
        for path in missing:
            print(f'- {path}')
        return 1
    print(f'OK: {len(REQUIRED)} required files present under {root}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
