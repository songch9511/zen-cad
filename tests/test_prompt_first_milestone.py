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
            'Do not embed Zen CAD repository paths, milestone folders, or CoBrA workspace paths',
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
                ROOT / 'docs/cobra_usage.md',
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

    def test_cobra_sync_installs_companion_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / 'zen-cad-kit'
            copy_repo_fixture(work)
            skills_root = Path(tmp) / 'cobra-skills'

            subprocess.run(
                [
                    sys.executable,
                    'scripts/setup_zen_cad.py',
                    '--sync-cobra-skill',
                    '--cobra-skill-dir',
                    str(skills_root / 'cad-spec'),
                    '--skip-validation',
                ],
                cwd=work,
                text=True,
                capture_output=True,
                check=True,
            )

            for skill_name in SHIPPED_SKILLS:
                self.assertTrue((skills_root / skill_name / 'SKILL.md').exists(), skill_name)
                source_dir = work / 'skills' / skill_name
                for source_file in (path for path in source_dir.rglob('*') if path.is_file()):
                    rel = source_file.relative_to(source_dir)
                    self.assertTrue((skills_root / skill_name / rel).exists(), f'{skill_name}/{rel}')
                context = skills_root / skill_name / 'ZEN_CAD_WORKSPACE.md'
                self.assertTrue(context.exists(), skill_name)
                context_text = context.read_text(encoding='utf-8')
                self.assertIn(f'Repository root: {work.resolve()}', context_text)
                self.assertIn('Start new CAD work with /cad-spec', context_text)
                self.assertIn('The CoBrA daemon/session cwd is not the Zen CAD workspace contract.', context_text)
                self.assertIn('python3 "<repository-root>/scripts/new_milestone.py" --root "<repository-root>" --request "<goal>"', context_text)


if __name__ == '__main__':
    unittest.main()
