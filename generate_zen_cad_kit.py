#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
from pathlib import Path
from textwrap import dedent

ROOT = Path(__file__).resolve().parent
SOURCE_SKILL = Path('/Users/daniel/.cobra/workspace/skills/agentic-cad/SKILL.md')


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(dedent(content).lstrip(), encoding='utf-8')


def write_json(path: str, data: object) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def ensure_dir(path: str) -> None:
    (ROOT / path).mkdir(parents=True, exist_ok=True)


def copy_skill() -> None:
    if not SOURCE_SKILL.exists():
        raise FileNotFoundError(f'Missing source /agentic-cad skill: {SOURCE_SKILL}')
    target = ROOT / 'skills/agentic-cad/SKILL.md'
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE_SKILL, target)


def schema_object(required: list[str], properties: dict[str, object]) -> dict[str, object]:
    return {
        '$schema': 'https://json-schema.org/draft/2020-12/schema',
        'type': 'object',
        'additionalProperties': False,
        'required': required,
        'properties': properties,
    }


def main() -> None:
    copy_skill()

    write('VERSION', '0.3.0\n')
    write('CHANGELOG.md', '''
    # Changelog

    ## 0.3.0

    - Initial portable Zen CAD repo/template kit.
    - Embeds the current `/agentic-cad` source-of-truth skill.
    - Adds milestone templates, artifact schemas, checklists, prompts, and validation scripts.
    - Seeds a reference NEMA17 belt-driven linear actuator milestone.
    ''')
    write('LICENSE', '''
    MIT License

    Copyright (c) 2026 Zen CAD contributors

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in all
    copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
    SOFTWARE.
    ''')
    write('README.md', '''
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
    ''')

    docs = {
        'docs/philosophy.md': '''
        # Philosophy

        Zen CAD treats mechanical CAD as an evidence-producing workflow, not a single text-to-3D generation event. The repository standardizes how an agent frames requirements, researches parts, chooses source-first versus generate-second, creates custom CAD, records assembly relationships, validates artifacts, and reports limitations.
        ''',
        'docs/operating_principles.md': '''
        # Operating Principles

        - Use `/agentic-cad` as the top-level workflow.
        - Prefer milestones over one-off unstructured CAD tasks.
        - Keep sourced parts, generated custom parts, and proxies visibly separate.
        - Record assumptions and limitations where they occur.
        - Do not claim engineering certification from CAD geometry alone.
        - End every milestone with machine-readable evidence and a human-readable report.
        ''',
        'docs/source_first_generate_second.md': '''
        # Source First, Generate Second

        Standard components should be sourced through credible catalogs, datasheets, manufacturer STEP downloads, or STEP Part RAG before any attempt to generate them. Custom generation is reserved for design-specific parts and assembly glue. If a standard component must be generated temporarily, mark it as `placeholder_proxy` and non-final.
        ''',
        'docs/completion_evidence.md': '''
        # Completion Evidence

        A milestone is not complete because a screenshot looks plausible. Completion requires reproducible artifacts:

        - required files exist in the milestone folder;
        - JSON artifacts pass schema validation;
        - CAD source and export paths are recorded;
        - CONTACT_MAP and CONNECTIONS reference known parts;
        - BOM distinguishes sourced, custom, semi-standard, and proxy parts;
        - validation report states checks, results, failures, and limitations;
        - final engineering report separates verified facts from assumptions.
        ''',
        'docs/milestone_protocol.md': '''
        # Milestone Protocol

        A Zen CAD milestone is an independently scoped CAD job inside the repository. Each milestone should contain requirements, research, part classification, selected parts, custom CAD handoff, assembly metadata, validation evidence, BOM, and final report. Use `scripts/new_milestone.py` to create new milestones from `milestones/_template`.
        ''',
        'docs/environment_setup.md': '''
        # Environment Setup

        Minimum requirements:

        - Python 3.10+
        - no required third-party Python package for metadata validation
        - a CAD generator/exporter appropriate to the task
        - optional JSON Schema package for stricter schema checks; the bundled script includes fallback validation for required fields and object structure
        ''',
        'docs/cobra_usage.md': '''
        # CoBrA Usage

        1. Ensure `/agentic-cad` is installed from `skills/agentic-cad/SKILL.md`.
        2. Start from `prompts/project_kickoff.md` for a new workspace or `prompts/new_milestone.md` for a new CAD job.
        3. Keep standard parts source-first and custom geometry generate-second.
        4. Require `scripts/check_required_files.py`, `scripts/check_json_schemas.py`, and `scripts/validate_milestone.py` evidence before reporting completion.
        ''',
        'docs/non_cobra_usage.md': '''
        # Non-CoBrA Usage

        Zen CAD can be used in any agentic environment that can read Markdown, edit files, run scripts, and create CAD artifacts. Treat `skills/agentic-cad/SKILL.md` as the main operating manual and the files in `prompts/` as task entrypoints.
        ''',
    }
    for path, content in docs.items():
        write(path, content)

    prompts = {
        'prompts/project_kickoff.md': '''
        # Zen CAD Project Kickoff Prompt

        Use `/agentic-cad` as the top-level workflow. Treat this repository as a portable Zen CAD operating environment, not a one-off text-to-CAD task. Preserve the source-first/generate-second rule, create CAD jobs as milestones, and require validation-script evidence before completion claims.

        First response requirements:

        - confirm the milestone target and assumptions;
        - identify standard/off-the-shelf parts to source first;
        - identify likely custom CAD parts;
        - name required artifacts and validation evidence;
        - do not generate standard parts as final geometry without sourcing evidence.
        ''',
        'prompts/new_milestone.md': '''
        # New Milestone Prompt

        Create a new Zen CAD milestone for the requested mechanical design. Use `scripts/new_milestone.py --id <id> --title <title>` or manually copy `milestones/_template`. Fill the required artifacts progressively and validate with:

        ```bash
        python3 scripts/check_required_files.py .
        python3 scripts/check_json_schemas.py .
        python3 scripts/validate_milestone.py milestones/<id>
        ```
        ''',
        'prompts/validation_review.md': '''
        # Validation Review Prompt

        Review the milestone using evidence only. Check required files, JSON schema validity, part classification completeness, selected part sourcing evidence, CONTACT_MAP/CONNECTIONS references, BOM consistency, and final report limitations. Screenshots or GLB previews may support human review but must not be treated as completion evidence.
        ''',
        'prompts/release_review.md': '''
        # Release Review Prompt

        Prepare a Zen CAD release only after required files, schemas, reference milestone, and documentation pass validation. Confirm the release preserves `/agentic-cad` as source of truth and does not include private machine-specific paths except documented examples.
        ''',
        'prompts/feedback_to_agentic_cad_skill.md': '''
        # Feedback to `/agentic-cad`

        Summarize any workflow improvement discovered during a Zen CAD milestone. Include the milestone id, failure or friction, proposed skill change, evidence, and whether the change affects source-first/generate-second, Part RAG fallback, validation evidence, or final reporting.
        ''',
    }
    for path, content in prompts.items():
        write(path, content)

    write('templates/PROJECT_MANIFEST.yaml', '''
    name: Zen CAD Workspace
    version: 0.3.0
    workflow_skill: /agentic-cad
    principles:
      - source_first_generate_second
      - standard_parts_are_sourced_before_generated
      - viewer_artifacts_are_not_completion_evidence
      - step_geometry_is_not_engineering_certification
    default_milestone_root: milestones
    ''')
    write('templates/milestone.yaml', '''
    id: REPLACE_WITH_MILESTONE_ID
    title: REPLACE_WITH_TITLE
    status: draft
    workflow: /agentic-cad
    created_at: REPLACE_WITH_DATE
    deliverables:
      - requirements_brief
      - part_classification_table
      - selected_parts_manifest
      - custom_cad_handoff
      - contact_map
      - connections
      - validation_report
      - bom
      - final_engineering_report
    ''')
    write('templates/requirements_brief.md', '''
    # Requirements Brief

    ## Goal

    TBD

    ## Functional requirements

    - TBD

    ## Constraints and assumptions

    - TBD

    ## Completion evidence

    - Required JSON artifacts pass schema validation.
    - CAD source/export paths are recorded.
    - BOM and final report distinguish verified facts from assumptions.
    ''')
    write('templates/part_classification_table.md', '''
    # Part Classification Table

    | Part ID | Name | Classification | Source-first query | Custom generation allowed? | Notes |
    | --- | --- | --- | --- | --- | --- |
    | P-001 | TBD | off_the_shelf | TBD | no | TBD |
    ''')
    write_json('templates/selected_parts_manifest.json', {
        'milestone_id': 'REPLACE_WITH_MILESTONE_ID',
        'parts': [
            {
                'part_id': 'P-001',
                'name': 'Example sourced part',
                'classification': 'off_the_shelf',
                'manufacturer': 'TBD',
                'part_number': 'TBD',
                'source_url': 'TBD',
                'datasheet_url': 'TBD',
                'step_path': '02_parts/step/example.step',
                'geometry_match': False,
                'engineering_rating_verified': False,
                'limitations': ['example placeholder']
            }
        ]
    })
    write('templates/custom_cad_handoff.yaml', '''
    milestone_id: REPLACE_WITH_MILESTONE_ID
    workflow: /spec-to-cad
    prohibited_generation:
      - sourced standard/catalog parts listed in selected_parts_manifest.json
    custom_parts:
      - part_id: C-001
        name: TBD custom bracket
        purpose: TBD
        interfaces: []
        dimensions: TBD
        material_assumption: TBD
        validation_criteria: []
    ''')
    write_json('templates/contact_map.json', {
        'milestone_id': 'REPLACE_WITH_MILESTONE_ID',
        'contacts': [
            {
                'contact_id': 'CT-001',
                'part_a': 'P-001',
                'part_b': 'C-001',
                'type': 'mounting_surface',
                'expected_clearance_mm': 0.0,
                'notes': 'example contact'
            }
        ]
    })
    write_json('templates/connections.json', {
        'milestone_id': 'REPLACE_WITH_MILESTONE_ID',
        'connections': [
            {
                'connection_id': 'CN-001',
                'parts': ['P-001', 'C-001'],
                'type': 'fastened_joint',
                'degrees_of_freedom': 'fixed',
                'fasteners': [],
                'notes': 'example connection'
            }
        ]
    })
    write_json('templates/validation_report.json', {
        'milestone_id': 'REPLACE_WITH_MILESTONE_ID',
        'status': 'draft',
        'checks': [
            {
                'check_id': 'CHK-001',
                'name': 'Required files exist',
                'result': 'not_run',
                'evidence': '',
                'limitations': []
            }
        ],
        'summary': 'TBD'
    })
    write('templates/bom.csv', '''
    part_id,name,classification,quantity,manufacturer,part_number,source_url,step_path,engineering_rating_verified,notes
    P-001,Example sourced part,off_the_shelf,1,TBD,TBD,TBD,02_parts/step/example.step,false,placeholder row
    ''')
    write('templates/final_engineering_report.md', '''
    # Final Engineering Report

    ## Summary

    TBD

    ## Verified evidence

    - TBD

    ## CAD-validated only

    - TBD

    ## Assumptions and limitations

    - TBD

    ## Next engineering work

    - TBD
    ''')

    write_json('schemas/selected_parts_manifest.schema.json', schema_object(
        ['milestone_id', 'parts'],
        {
            'milestone_id': {'type': 'string', 'minLength': 1},
            'parts': {
                'type': 'array',
                'items': {
                    'type': 'object',
                    'required': ['part_id', 'name', 'classification', 'geometry_match', 'engineering_rating_verified'],
                    'properties': {
                        'part_id': {'type': 'string'},
                        'name': {'type': 'string'},
                        'classification': {'enum': ['off_the_shelf', 'semi_standard_configurable', 'custom_design_specific', 'placeholder_proxy']},
                        'manufacturer': {'type': 'string'},
                        'part_number': {'type': 'string'},
                        'source_url': {'type': 'string'},
                        'datasheet_url': {'type': 'string'},
                        'step_path': {'type': 'string'},
                        'geometry_match': {'type': 'boolean'},
                        'engineering_rating_verified': {'type': 'boolean'},
                        'limitations': {'type': 'array', 'items': {'type': 'string'}},
                    },
                    'additionalProperties': True,
                },
            },
        },
    ))
    write_json('schemas/contact_map.schema.json', schema_object(
        ['milestone_id', 'contacts'],
        {
            'milestone_id': {'type': 'string'},
            'contacts': {'type': 'array', 'items': {'type': 'object', 'required': ['contact_id', 'part_a', 'part_b', 'type'], 'additionalProperties': True}},
        },
    ))
    write_json('schemas/connections.schema.json', schema_object(
        ['milestone_id', 'connections'],
        {
            'milestone_id': {'type': 'string'},
            'connections': {'type': 'array', 'items': {'type': 'object', 'required': ['connection_id', 'parts', 'type'], 'additionalProperties': True}},
        },
    ))
    write_json('schemas/validation_report.schema.json', schema_object(
        ['milestone_id', 'status', 'checks', 'summary'],
        {
            'milestone_id': {'type': 'string'},
            'status': {'enum': ['draft', 'pass', 'fail', 'blocked']},
            'checks': {'type': 'array', 'items': {'type': 'object', 'required': ['check_id', 'name', 'result'], 'additionalProperties': True}},
            'summary': {'type': 'string'},
        },
    ))
    write_json('schemas/bom.schema.json', schema_object(
        ['columns'],
        {'columns': {'type': 'array', 'items': {'type': 'string'}}},
    ))
    write_json('schemas/bom.columns.json', {
        'columns': ['part_id', 'name', 'classification', 'quantity', 'manufacturer', 'part_number', 'source_url', 'step_path', 'engineering_rating_verified', 'notes']
    })

    checklists = {
        'checklists/intake_checklist.md': ['Design goal captured', 'Units and envelope recorded', 'Loads/speeds/travel assumptions logged', 'Completion evidence named'],
        'checklists/sourcing_checklist.md': ['Standard parts identified', 'Part RAG/catalog queries recorded', 'Datasheet/source URLs captured', 'Geometry match separated from rating verification'],
        'checklists/custom_cad_checklist.md': ['Only design-specific parts generated', 'Interfaces to sourced parts specified', 'Materials/manufacturing assumptions marked', 'Validation criteria listed'],
        'checklists/assembly_checklist.md': ['CONTACT_MAP complete', 'CONNECTIONS complete', 'Coordinate frames and mating features recorded', 'Proxy parts marked non-final'],
        'checklists/validation_checklist.md': ['Required files exist', 'JSON schemas pass', 'CAD/export paths recorded', 'Screenshots not used as sole evidence'],
        'checklists/release_checklist.md': ['README current', 'Skill embedded', 'Reference milestone validates', 'Private paths reviewed', 'Changelog updated'],
    }
    for path, items in checklists.items():
        write(path, '# ' + Path(path).stem.replace('_', ' ').title() + '\n\n' + '\n'.join(f'- [ ] {item}' for item in items) + '\n')

    write('scripts/check_required_files.py', r'''
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
    ''')

    write('scripts/check_json_schemas.py', r'''
    #!/usr/bin/env python3
    from __future__ import annotations

    import csv
    import json
    import sys
    from pathlib import Path

    JSON_PAIRS = [
        ('schemas/selected_parts_manifest.schema.json', 'templates/selected_parts_manifest.json'),
        ('schemas/contact_map.schema.json', 'templates/contact_map.json'),
        ('schemas/connections.schema.json', 'templates/connections.json'),
        ('schemas/validation_report.schema.json', 'templates/validation_report.json'),
        ('schemas/selected_parts_manifest.schema.json', 'milestones/_template/02_parts/selected_parts_manifest.json'),
        ('schemas/contact_map.schema.json', 'milestones/_template/04_assembly/contact_map.json'),
        ('schemas/connections.schema.json', 'milestones/_template/04_assembly/connections.json'),
        ('schemas/validation_report.schema.json', 'milestones/_template/05_validation/validation_report.json'),
        ('schemas/selected_parts_manifest.schema.json', 'milestones/001_nema17_belt_linear_actuator/02_parts/selected_parts_manifest.json'),
        ('schemas/contact_map.schema.json', 'milestones/001_nema17_belt_linear_actuator/04_assembly/contact_map.json'),
        ('schemas/connections.schema.json', 'milestones/001_nema17_belt_linear_actuator/04_assembly/connections.json'),
        ('schemas/validation_report.schema.json', 'milestones/001_nema17_belt_linear_actuator/05_validation/validation_report.json'),
    ]

    REQUIRED_BY_SCHEMA = {
        'selected_parts_manifest.schema.json': ['milestone_id', 'parts'],
        'contact_map.schema.json': ['milestone_id', 'contacts'],
        'connections.schema.json': ['milestone_id', 'connections'],
        'validation_report.schema.json': ['milestone_id', 'status', 'checks', 'summary'],
    }

    def validate_required(schema_path: Path, data_path: Path) -> list[str]:
        data = json.loads(data_path.read_text(encoding='utf-8'))
        required = REQUIRED_BY_SCHEMA.get(schema_path.name, [])
        errors = []
        if not isinstance(data, dict):
            errors.append('top-level JSON is not an object')
            return errors
        for key in required:
            if key not in data:
                errors.append(f'missing required key: {key}')
        return errors

    def validate_bom(root: Path) -> list[str]:
        expected = json.loads((root / 'schemas/bom.columns.json').read_text(encoding='utf-8'))['columns']
        paths = ['templates/bom.csv', 'milestones/_template/06_bom/bom.csv', 'milestones/001_nema17_belt_linear_actuator/06_bom/bom.csv']
        errors = []
        for rel in paths:
            with (root / rel).open(newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)
            if header != expected:
                errors.append(f'{rel}: header mismatch {header!r}')
        return errors

    def main() -> int:
        root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
        errors = []
        for schema_rel, data_rel in JSON_PAIRS:
            schema_path = root / schema_rel
            data_path = root / data_rel
            json.loads(schema_path.read_text(encoding='utf-8'))
            errors.extend(f'{data_rel}: {err}' for err in validate_required(schema_path, data_path))
        errors.extend(validate_bom(root))
        if errors:
            print('Schema validation failed:')
            for error in errors:
                print(f'- {error}')
            return 1
        print(f'OK: {len(JSON_PAIRS)} JSON artifacts and BOM CSV headers validated')
        return 0

    if __name__ == '__main__':
        raise SystemExit(main())
    ''')

    write('scripts/validate_milestone.py', r'''
    #!/usr/bin/env python3
    from __future__ import annotations

    import csv
    import json
    import sys
    from pathlib import Path

    REQUIRED = [
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

    def main() -> int:
        milestone = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
        missing = [p for p in REQUIRED if not (milestone / p).exists()]
        errors = []
        if missing:
            errors.extend(f'missing {p}' for p in missing)
        for rel in ['02_parts/selected_parts_manifest.json', '04_assembly/contact_map.json', '04_assembly/connections.json', '05_validation/validation_report.json']:
            try:
                data = json.loads((milestone / rel).read_text(encoding='utf-8'))
            except Exception as exc:
                errors.append(f'{rel}: invalid JSON: {exc}')
                continue
            if not isinstance(data, dict) or not data.get('milestone_id'):
                errors.append(f'{rel}: missing milestone_id')
        if (milestone / '06_bom/bom.csv').exists():
            with (milestone / '06_bom/bom.csv').open(newline='', encoding='utf-8') as f:
                header = next(csv.reader(f))
            if 'part_id' not in header or 'classification' not in header:
                errors.append('06_bom/bom.csv: missing required columns')
        if errors:
            print(f'Milestone validation failed: {milestone}')
            for error in errors:
                print(f'- {error}')
            return 1
        print(f'OK: milestone validates: {milestone}')
        return 0

    if __name__ == '__main__':
        raise SystemExit(main())
    ''')

    write('scripts/new_milestone.py', r'''
    #!/usr/bin/env python3
    from __future__ import annotations

    import argparse
    import shutil
    from datetime import date
    from pathlib import Path

    def main() -> int:
        parser = argparse.ArgumentParser(description='Create a new Zen CAD milestone from the template.')
        parser.add_argument('--id', required=True, help='Milestone id, e.g. 002_robot_gripper')
        parser.add_argument('--title', required=True, help='Human-readable milestone title')
        parser.add_argument('--root', default='.', help='Zen CAD repository root')
        args = parser.parse_args()

        root = Path(args.root).resolve()
        template = root / 'milestones/_template'
        target = root / f'milestones/{args.id}'
        if target.exists():
            raise SystemExit(f'ERROR: milestone already exists: {target}')
        shutil.copytree(template, target)
        milestone_file = target / 'milestone.yaml'
        text = milestone_file.read_text(encoding='utf-8')
        text = text.replace('REPLACE_WITH_MILESTONE_ID', args.id).replace('REPLACE_WITH_TITLE', args.title).replace('REPLACE_WITH_DATE', date.today().isoformat())
        milestone_file.write_text(text, encoding='utf-8')
        for rel in ['02_parts/selected_parts_manifest.json', '04_assembly/contact_map.json', '04_assembly/connections.json', '05_validation/validation_report.json']:
            path = target / rel
            path.write_text(path.read_text(encoding='utf-8').replace('REPLACE_WITH_MILESTONE_ID', args.id), encoding='utf-8')
        print(f'Created milestone: {target}')
        return 0

    if __name__ == '__main__':
        raise SystemExit(main())
    ''')

    write('scripts/export_release_package.py', r'''
    #!/usr/bin/env python3
    from __future__ import annotations

    import shutil
    import sys
    from pathlib import Path

    def main() -> int:
        root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
        version = (root / 'VERSION').read_text(encoding='utf-8').strip()
        out = root / 'releases' / f'zen-cad-v{version}'
        out.mkdir(parents=True, exist_ok=True)
        for name in ['README.md', 'VERSION', 'CHANGELOG.md', 'docs', 'skills', 'prompts', 'templates', 'schemas', 'checklists', 'scripts', 'milestones/_template']:
            src = root / name
            dst = out / name
            if src.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            elif src.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        print(f'Exported release package: {out}')
        return 0

    if __name__ == '__main__':
        raise SystemExit(main())
    ''')

    # Milestone template directories and files.
    for rel in [
        'milestones/_template/00_requirements',
        'milestones/_template/01_research',
        'milestones/_template/02_parts/step',
        'milestones/_template/03_cad/src',
        'milestones/_template/03_cad/exports',
        'milestones/_template/04_assembly',
        'milestones/_template/05_validation',
        'milestones/_template/06_bom',
        'milestones/_template/07_report',
    ]:
        ensure_dir(rel)
    shutil.copyfile(ROOT / 'templates/milestone.yaml', ROOT / 'milestones/_template/milestone.yaml')
    shutil.copyfile(ROOT / 'templates/requirements_brief.md', ROOT / 'milestones/_template/00_requirements/requirements_brief.md')
    write('milestones/_template/01_research/research_log.md', '# Research Log\n\n- TBD\n')
    shutil.copyfile(ROOT / 'templates/part_classification_table.md', ROOT / 'milestones/_template/02_parts/part_classification_table.md')
    shutil.copyfile(ROOT / 'templates/selected_parts_manifest.json', ROOT / 'milestones/_template/02_parts/selected_parts_manifest.json')
    shutil.copyfile(ROOT / 'templates/custom_cad_handoff.yaml', ROOT / 'milestones/_template/03_cad/custom_cad_handoff.yaml')
    shutil.copyfile(ROOT / 'templates/contact_map.json', ROOT / 'milestones/_template/04_assembly/contact_map.json')
    shutil.copyfile(ROOT / 'templates/connections.json', ROOT / 'milestones/_template/04_assembly/connections.json')
    shutil.copyfile(ROOT / 'templates/validation_report.json', ROOT / 'milestones/_template/05_validation/validation_report.json')
    shutil.copyfile(ROOT / 'templates/bom.csv', ROOT / 'milestones/_template/06_bom/bom.csv')
    shutil.copyfile(ROOT / 'templates/final_engineering_report.md', ROOT / 'milestones/_template/07_report/final_engineering_report.md')

    # Reference milestone seed.
    ref = 'milestones/001_nema17_belt_linear_actuator'
    for rel in ['00_requirements', '01_research', '02_parts/step', '03_cad/src', '03_cad/exports', '04_assembly', '05_validation', '06_bom', '07_report']:
        ensure_dir(f'{ref}/{rel}')
    write(f'{ref}/milestone.yaml', '''
    id: 001_nema17_belt_linear_actuator
    title: NEMA17 belt-driven linear actuator
    status: seed
    workflow: /agentic-cad
    created_at: 2026-06-01
    deliverables:
      - requirements_brief
      - part_classification_table
      - selected_parts_manifest
      - custom_cad_handoff
      - contact_map
      - connections
      - validation_report
      - bom
      - final_engineering_report
    ''')
    write(f'{ref}/00_requirements/requirements_brief.md', '''
    # Requirements Brief — NEMA17 Belt-Driven Linear Actuator

    ## Goal

    Seed a compact belt-driven linear actuator milestone that demonstrates the Zen CAD workflow. The design uses sourced standard components where possible and reserves custom CAD for plates, brackets, belt clamps, guards, and assembly glue.

    ## Initial assumptions

    - Motor class: NEMA17 stepper.
    - Motion: belt-driven linear travel.
    - Standard parts to source first: NEMA17 motor, GT2 belt, GT2 pulleys/idlers, linear rail or rods, bearings, fasteners.
    - Custom parts: motor mount, idler bracket, carriage plate, belt clamp, end plates, optional guard.

    ## Completion evidence

    This seed is a workflow scaffold, not a finished certified actuator. Future revisions must add sourced STEP files, CAD exports, kernel checks, and engineering calculations before claiming a complete design.
    ''')
    write(f'{ref}/01_research/research_log.md', '''
    # Research Log

    Seed queries:

    - NEMA17 stepper motor STEP datasheet mounting pattern
    - GT2 timing pulley STEP 20 tooth 5 mm bore
    - GT2 belt width 6 mm datasheet
    - MGN12 linear rail carriage STEP
    - miniature bearing/idler pulley STEP

    Ratings and dimensions are intentionally unverified in this seed until real catalog sources are attached.
    ''')
    write(f'{ref}/02_parts/part_classification_table.md', '''
    # Part Classification Table

    | Part ID | Name | Classification | Source-first query | Custom generation allowed? | Notes |
    | --- | --- | --- | --- | --- | --- |
    | P-001 | NEMA17 stepper motor | off_the_shelf | NEMA17 stepper motor STEP datasheet | no | Must source catalog geometry. |
    | P-002 | GT2 drive pulley | off_the_shelf | GT2 pulley STEP 20T 5mm bore | no | Verify bore/tooth count. |
    | P-003 | GT2 belt | off_the_shelf | GT2 belt 6mm datasheet | no | Belt length depends on travel. |
    | P-004 | Linear rail/carriage | off_the_shelf | MGN12 rail carriage STEP | no | Rail length TBD. |
    | C-001 | Motor mount plate | custom_design_specific | n/a | yes | Generated custom geometry. |
    | C-002 | Idler bracket | custom_design_specific | n/a | yes | Generated custom geometry. |
    | C-003 | Carriage adapter plate | custom_design_specific | n/a | yes | Generated custom geometry. |
    | X-001 | Unverified idler proxy | placeholder_proxy | idler pulley bearing STEP | temporary only | Non-final until sourced. |
    ''')
    write_json(f'{ref}/02_parts/selected_parts_manifest.json', {
        'milestone_id': '001_nema17_belt_linear_actuator',
        'parts': [
            {'part_id': 'P-001', 'name': 'NEMA17 stepper motor', 'classification': 'off_the_shelf', 'manufacturer': 'TBD', 'part_number': 'TBD', 'source_url': 'TBD', 'datasheet_url': 'TBD', 'step_path': '02_parts/step/P-001_nema17_motor.step', 'geometry_match': False, 'engineering_rating_verified': False, 'limitations': ['seed placeholder; source not attached']},
            {'part_id': 'P-002', 'name': 'GT2 drive pulley', 'classification': 'off_the_shelf', 'manufacturer': 'TBD', 'part_number': 'TBD', 'source_url': 'TBD', 'datasheet_url': 'TBD', 'step_path': '02_parts/step/P-002_gt2_pulley.step', 'geometry_match': False, 'engineering_rating_verified': False, 'limitations': ['seed placeholder; tooth count and bore unverified']},
            {'part_id': 'X-001', 'name': 'Idler pulley proxy', 'classification': 'placeholder_proxy', 'manufacturer': 'TBD', 'part_number': 'TBD', 'source_url': 'TBD', 'datasheet_url': 'TBD', 'step_path': '02_parts/step/X-001_idler_proxy.step', 'geometry_match': False, 'engineering_rating_verified': False, 'limitations': ['proxy only; not final geometry']}
        ]
    })
    write(f'{ref}/03_cad/custom_cad_handoff.yaml', '''
    milestone_id: 001_nema17_belt_linear_actuator
    workflow: /spec-to-cad
    prohibited_generation:
      - P-001 NEMA17 stepper motor
      - P-002 GT2 drive pulley
      - P-003 GT2 belt
      - P-004 linear rail/carriage
    custom_parts:
      - part_id: C-001
        name: motor_mount_plate
        purpose: Mount NEMA17 motor to actuator frame with belt centerline alignment.
        interfaces: [P-001, P-002]
        dimensions: TBD after sourced motor/pulley dimensions
        material_assumption: aluminum plate or printed prototype, unverified
        validation_criteria: [mounting_hole_pattern_matches_sourced_motor, pulley_clearance_recorded]
      - part_id: C-002
        name: idler_bracket
        purpose: Hold idler pulley at belt return end.
        interfaces: [X-001]
        dimensions: TBD
        material_assumption: aluminum plate or printed prototype, unverified
        validation_criteria: [idler_axis_parallel_to_drive_pulley, belt_path_clearance_recorded]
      - part_id: C-003
        name: carriage_adapter_plate
        purpose: Connect belt clamp and payload interface to linear carriage.
        interfaces: [P-003, P-004]
        dimensions: TBD
        material_assumption: aluminum plate, unverified
        validation_criteria: [carriage_hole_pattern_matches_sourced_rail, belt_clamp_clearance_recorded]
    ''')
    write_json(f'{ref}/04_assembly/contact_map.json', {
        'milestone_id': '001_nema17_belt_linear_actuator',
        'contacts': [
            {'contact_id': 'CT-001', 'part_a': 'P-001', 'part_b': 'C-001', 'type': 'mounting_face', 'expected_clearance_mm': 0.0, 'notes': 'NEMA17 face to custom motor mount'},
            {'contact_id': 'CT-002', 'part_a': 'P-002', 'part_b': 'P-003', 'type': 'belt_to_pulley_mesh', 'expected_clearance_mm': 0.0, 'notes': 'GT2 belt engagement; seed only'},
            {'contact_id': 'CT-003', 'part_a': 'P-004', 'part_b': 'C-003', 'type': 'carriage_mounting_face', 'expected_clearance_mm': 0.0, 'notes': 'Carriage adapter to rail carriage'}
        ]
    })
    write_json(f'{ref}/04_assembly/connections.json', {
        'milestone_id': '001_nema17_belt_linear_actuator',
        'connections': [
            {'connection_id': 'CN-001', 'parts': ['P-001', 'C-001'], 'type': 'fastened_joint', 'degrees_of_freedom': 'fixed', 'fasteners': ['TBD M3 screws'], 'notes': 'NEMA17 mounting pattern to verify'},
            {'connection_id': 'CN-002', 'parts': ['P-002', 'P-001'], 'type': 'shaft_clamp_or_set_screw', 'degrees_of_freedom': 'rotates_with_motor_shaft', 'fasteners': ['pulley set screw TBD'], 'notes': 'Bore and shaft diameter unverified'},
            {'connection_id': 'CN-003', 'parts': ['P-003', 'C-003'], 'type': 'belt_clamp', 'degrees_of_freedom': 'fixed_to_carriage', 'fasteners': [], 'notes': 'Clamp geometry custom and TBD'}
        ]
    })
    write_json(f'{ref}/05_validation/validation_report.json', {
        'milestone_id': '001_nema17_belt_linear_actuator',
        'status': 'draft',
        'checks': [
            {'check_id': 'CHK-001', 'name': 'Seed required files exist', 'result': 'pass', 'evidence': 'Generated by Zen CAD kit scaffold and validated by scripts/validate_milestone.py.', 'limitations': []},
            {'check_id': 'CHK-002', 'name': 'Engineering ratings verified', 'result': 'blocked', 'evidence': 'No real datasheets attached in seed.', 'limitations': ['seed is not final engineering evidence']},
            {'check_id': 'CHK-003', 'name': 'CAD kernel checks', 'result': 'not_run', 'evidence': 'No final CAD generated in seed.', 'limitations': ['future milestone revision must run CAD load/export checks']}
        ],
        'summary': 'Reference seed validates workflow structure only; it does not certify actuator design.'
    })
    write(f'{ref}/06_bom/bom.csv', '''
    part_id,name,classification,quantity,manufacturer,part_number,source_url,step_path,engineering_rating_verified,notes
    P-001,NEMA17 stepper motor,off_the_shelf,1,TBD,TBD,TBD,02_parts/step/P-001_nema17_motor.step,false,seed placeholder
    P-002,GT2 drive pulley,off_the_shelf,1,TBD,TBD,TBD,02_parts/step/P-002_gt2_pulley.step,false,seed placeholder
    P-003,GT2 belt,off_the_shelf,1,TBD,TBD,TBD,,false,belt length TBD
    P-004,Linear rail/carriage,off_the_shelf,1,TBD,TBD,TBD,,false,rail length TBD
    C-001,Motor mount plate,custom_design_specific,1,,,,,false,custom CAD to generate
    C-002,Idler bracket,custom_design_specific,1,,,,,false,custom CAD to generate
    C-003,Carriage adapter plate,custom_design_specific,1,,,,,false,custom CAD to generate
    X-001,Idler pulley proxy,placeholder_proxy,1,TBD,TBD,TBD,02_parts/step/X-001_idler_proxy.step,false,non-final proxy
    ''')
    write(f'{ref}/07_report/final_engineering_report.md', '''
    # Final Engineering Report — NEMA17 Belt-Driven Linear Actuator Seed

    ## Summary

    This is a reference milestone seed showing how Zen CAD structures a sourcing-aware CAD job. It is not a completed actuator design.

    ## Verified evidence

    - Required milestone files are present.
    - JSON artifacts are structured for schema validation.
    - Standard parts are marked source-first.
    - Custom parts are limited to design-specific plates/brackets/adapters.

    ## CAD-validated only

    - No final CAD validation has been run in this seed.

    ## Assumptions and limitations

    - Catalog sources, STEP geometry, datasheets, belt length, travel, loads, speed, torque, and structural checks are unresolved.
    - STEP geometry, when later attached, will not by itself prove engineering rating or certification.
    - Viewer artifacts are not completion evidence.

    ## Next engineering work

    - Source real STEP/catalog parts.
    - Perform torque, belt, rail, bearing/idler, and bracket sizing.
    - Generate custom CAD only after sourced dimensions are known.
    - Run CAD kernel/export/interference checks and update the validation report.
    ''')

    ensure_dir('examples/nema17_belt_linear_actuator')
    write('examples/nema17_belt_linear_actuator/README.md', '''
    # NEMA17 Belt Linear Actuator Example

    See `milestones/001_nema17_belt_linear_actuator` for the reference seed milestone. The example is intentionally a scaffold: it demonstrates Zen CAD artifact structure and source-first decisions before real CAD generation.
    ''')
    ensure_dir('releases')


if __name__ == '__main__':
    main()
