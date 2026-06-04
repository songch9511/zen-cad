#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SHIPPED_SKILLS = [
    'agentic-cad',
    'assembly-layout',
    'cad-artifact-reviewer',
    'cad-handoff',
    'cad-spec',
    'interface-signatures',
    'manufacturing-preflight',
    'mechanism-kinematics',
    'self-evolving-producer-verifier',
    'source-step-parts',
    'spec-to-cad',
]


def copy_repo_fixture(target: Path) -> None:
    shutil.copytree(
        ROOT,
        target,
        ignore=shutil.ignore_patterns('.git', 'releases', 'tests', '__pycache__', '002_linear_actuator'),
    )


class PromptFirstMilestoneWorkflowTest(unittest.TestCase):
    def test_shipped_skills_have_release_versions(self) -> None:
        for skill_name in SHIPPED_SKILLS:
            text = (ROOT / f'skills/{skill_name}/SKILL.md').read_text(encoding='utf-8')
            self.assertIn('version: 0.8.0', text, skill_name)

    def test_text_to_cad_inspired_companion_skills_exist(self) -> None:
        expected = {
            'source-step-parts': [
                'selected_parts_manifest.json',
                'source_locked',
                './zen-cad source-lock milestones/<id>',
                'STEP geometry proves geometry only',
            ],
            'cad-artifact-reviewer': [
                'cad_generation',
                'step_load',
                'geometry_inspection',
                'evidence_check_ids',
                'metadata-only PASS claims',
            ],
            'manufacturing-preflight': [
                'manufacturing_preflight',
                'DXF',
                'STL/3MF',
                'does not replace `cad_generation`, `step_load`, or `geometry_inspection`',
            ],
            'mechanism-kinematics': [
                'kinematic_contract',
                'URDF',
                'SDF',
                'SRDF',
                'joints, frames, axes, limits',
            ],
        }
        for skill_name, phrases in expected.items():
            text = (ROOT / f'skills/{skill_name}/SKILL.md').read_text(encoding='utf-8')
            for phrase in phrases:
                self.assertIn(phrase, text, skill_name)

    def test_cad_spec_is_core_spec_first_entrypoint(self) -> None:
        text = (ROOT / 'skills/cad-spec/SKILL.md').read_text(encoding='utf-8')
        for phrase in [
            'spec the assembly contract before generating CAD',
            'Interface Primitives',
            'Locked Layout Facts',
            'Proceed Gate',
            'Downstream CAD Handoff',
            'Do not source-lock or crawl for catalog parts before writing the layout spec',
            'Do not embed Zen CAD repository paths, milestone folders, or harness workspace paths',
        ]:
            self.assertIn(phrase, text)
        for phrase in [
            'milestones/<id>',
            './zen-cad validate',
            'selected_parts_manifest.json',
            'validation_report.json',
        ]:
            self.assertNotIn(phrase, text)

    def test_focused_08_skills_are_local_and_non_generating(self) -> None:
        expected = {
            'assembly-layout': [
                'it focuses only on how parts locate, mate, move, clear, and connect',
                'does not generate CAD',
                'locked facts',
            ],
            'interface-signatures': [
                'does not source-lock catalog parts',
                'trusted_for_layout',
                'must confirm before final',
            ],
            'cad-handoff': [
                'adapter-specific',
                'Preserve locked facts verbatim',
                'Stop conditions',
            ],
        }
        for skill_name, phrases in expected.items():
            text = (ROOT / f'skills/{skill_name}/SKILL.md').read_text(encoding='utf-8')
            for phrase in phrases:
                self.assertIn(phrase, text, skill_name)

    def test_spec_to_cad_is_milestone_first_and_text_to_cad_first(self) -> None:
        text = (ROOT / 'skills/spec-to-cad/SKILL.md').read_text(encoding='utf-8')
        required_phrases = [
            'Milestone-first CAD execution skill',
            'earthtojake/text-to-cad',
            'scripts/step',
            'scripts/inspect refs',
            'scripts/snapshot',
            '03_cad/custom_cad_handoff.yaml',
            '05_validation/validation_report.json',
            'cad_generation',
            'step_load',
            'geometry_inspection',
            'size_bytes',
            'sha256',
            'evidence_check_ids',
            './zen-cad validate --level completion milestones/<id>',
        ]
        for phrase in required_phrases:
            self.assertIn(phrase, text)
        forbidden_phrases = [
            'GFL/test_materials',
            'high_speed_powder_mill',
            'PM160',
            '/Users/vanta',
        ]
        for phrase in forbidden_phrases:
            self.assertNotIn(phrase, text)

    def test_agentic_cad_is_deprecated_compatibility_shim(self) -> None:
        text = (ROOT / 'skills/agentic-cad/SKILL.md').read_text(encoding='utf-8')
        for phrase in [
            'Deprecated Zen CAD compatibility entrypoint',
            '`agentic-cad` is deprecated in Zen CAD 0.8.0',
            '/cad-spec',
            '/assembly-layout',
            '/interface-signatures',
            '/cad-handoff',
            'This shim must stay small',
        ]:
            self.assertIn(phrase, text)
        for phrase in [
            '00_requirements/requirements_brief.md',
            '02_parts/selected_parts_manifest.json',
            '05_validation/validation_report.json',
            'evidence_type: "environment"',
        ]:
            self.assertNotIn(phrase, text)

    def test_self_evolving_skill_has_portable_fallback(self) -> None:
        text = (ROOT / 'skills/self-evolving-producer-verifier/SKILL.md').read_text(encoding='utf-8')
        for phrase in [
            'optional harness primitives',
            'Portable Fallback',
            'producer_approach.md',
            'verifier_report.md',
            'If it does not, use the portable file-based fallback',
        ]:
            self.assertIn(phrase, text)

    def test_cad_spec_first_docs_and_legacy_milestone_helper(self) -> None:
        searchable_text = '\n'.join(
            path.read_text(encoding='utf-8')
            for path in [
                ROOT / 'README.md',
                ROOT / 'docs/generic_usage.md',
                ROOT / 'docs/environment_setup.md',
                ROOT / 'docs/operating_principles.md',
                ROOT / 'prompts/project_kickoff.md',
                ROOT / 'prompts/new_milestone.md',
                ROOT / 'skills/cad-spec/SKILL.md',
                ROOT / 'templates/milestone.yaml',
            ]
        ).casefold()
        for phrase in [
            'use `/cad-spec` as the default starting skill',
            'cad-native spec',
            'low-detail layout proxy',
            'proceed gate',
            'legacy milestone',
            'python3 scripts/new_milestone.py --request "<goal>"',
            'workflow: /cad-spec',
        ]:
            self.assertIn(phrase.casefold(), searchable_text)
        self.assertNotIn('003_gearbox', searchable_text)
        self.assertNotIn('create the milestone with `--milestone-request` before editing artifacts', searchable_text)

        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / 'zen-cad-kit'
            copy_repo_fixture(work)
            completed = subprocess.run(
                [sys.executable, 'scripts/new_milestone.py', '--request', '기어 박스를 만들고 싶어'],
                cwd=work,
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertIn('Milestone id: 003_gearbox', completed.stdout)
            self.assertIn('Title: Gearbox', completed.stdout)
            created_milestone = work / 'milestones/003_gearbox/milestone.yaml'
            self.assertTrue(created_milestone.exists())
            self.assertIn('workflow: /cad-spec', created_milestone.read_text(encoding='utf-8'))

            explicit = subprocess.run(
                [
                    sys.executable,
                    'scripts/new_milestone.py',
                    '--id',
                    '003_custom_fixture',
                    '--title',
                    'Custom fixture',
                ],
                cwd=work,
                text=True,
                capture_output=True,
                check=True,
            )
            self.assertIn('Milestone id: 003_custom_fixture', explicit.stdout)
            self.assertIn('Title: Custom fixture', explicit.stdout)

    def test_required_file_check_covers_all_milestones(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / 'zen-cad-kit'
            copy_repo_fixture(work)
            subprocess.run(
                [
                    sys.executable,
                    'scripts/new_milestone.py',
                    '--id',
                    '002_required_files_test',
                    '--title',
                    'Required files test',
                ],
                cwd=work,
                text=True,
                capture_output=True,
                check=True,
            )
            missing = work / 'milestones/002_required_files_test/01_research/research_log.md'
            missing.unlink()

            completed = subprocess.run(
                [sys.executable, 'scripts/check_required_files.py', '.'],
                cwd=work,
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn('milestones/002_required_files_test/01_research/research_log.md', completed.stdout)

    def test_schema_check_rejects_actual_schema_violations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / 'zen-cad-kit'
            copy_repo_fixture(work)
            subprocess.run(
                [
                    sys.executable,
                    'scripts/new_milestone.py',
                    '--id',
                    '002_schema_test',
                    '--title',
                    'Schema test',
                ],
                cwd=work,
                text=True,
                capture_output=True,
                check=True,
            )
            manifest = work / 'milestones/002_schema_test/02_parts/selected_parts_manifest.json'
            data = json.loads(manifest.read_text(encoding='utf-8'))
            data['unexpected'] = True
            data['parts'][0]['geometry_match'] = 'false'
            manifest.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')

            completed = subprocess.run(
                [sys.executable, 'scripts/check_json_schemas.py', '.'],
                cwd=work,
                text=True,
                capture_output=True,
            )

            self.assertNotEqual(completed.returncode, 0)
            self.assertIn('additional property not allowed: unexpected', completed.stdout)
            self.assertIn('$.parts[0].geometry_match: expected boolean, got string', completed.stdout)

    def test_no_harness_specific_workspace_binding_surface(self) -> None:
        forbidden = ['Co' + 'BrA', 'co' + 'bra', 'ZEN_CAD' + '_WORKSPACE', 'with-' + 'co' + 'bra', 'CO' + 'BRA' + '_']
        checked_roots = [
            ROOT / 'README.md',
            ROOT / 'docs',
            ROOT / 'plugins',
            ROOT / 'prompts',
            ROOT / 'scripts',
            ROOT / 'skills',
            ROOT / 'templates',
        ]
        files: list[Path] = []
        text_suffixes = {'.md', '.py', '.yaml', '.yml', '.json', '.csv', '.txt'}
        for root in checked_roots:
            if root.is_file():
                files.append(root)
            else:
                files.extend(path for path in root.rglob('*') if path.is_file() and path.suffix in text_suffixes)
        for path in files:
            text = path.read_text(encoding='utf-8')
            for phrase in forbidden:
                self.assertNotIn(phrase, text, str(path.relative_to(ROOT)))


if __name__ == '__main__':
    unittest.main()
