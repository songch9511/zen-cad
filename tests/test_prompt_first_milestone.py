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


def copy_repo_fixture(target: Path) -> None:
    shutil.copytree(
        ROOT,
        target,
        ignore=shutil.ignore_patterns('.git', 'releases', 'tests', '__pycache__', '002_linear_actuator'),
    )


class PromptFirstMilestoneWorkflowTest(unittest.TestCase):
    def test_shipped_skills_have_release_versions(self) -> None:
        for skill_name in ['agentic-cad', 'cad-artifact-reviewer', 'manufacturing-preflight', 'mechanism-kinematics', 'spec-to-cad', 'self-evolving-producer-verifier', 'source-step-parts']:
            text = (ROOT / f'skills/{skill_name}/SKILL.md').read_text(encoding='utf-8')
            self.assertIn('version: 0.6.6', text, skill_name)

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

    def test_agentic_cad_routes_to_companion_skills(self) -> None:
        text = (ROOT / 'skills/agentic-cad/SKILL.md').read_text(encoding='utf-8')
        for phrase in [
            'Companion skill routing',
            '/source-step-parts',
            '/cad-artifact-reviewer',
            '/manufacturing-preflight',
            '/mechanism-kinematics',
            'Do not load every companion skill automatically',
        ]:
            self.assertIn(phrase, text)

    def test_agentic_cad_startup_does_not_conflate_cobra_cwd_with_workspace(self) -> None:
        text = (ROOT / 'skills/agentic-cad/SKILL.md').read_text(encoding='utf-8')
        for phrase in [
            'after this skill resolves a Zen CAD workspace root',
            'The CoBrA daemon cwd, CoBrA session cwd, and terminal cwd are not the Zen CAD workspace contract',
            'Use the resolved Zen CAD root as the command cwd or pass it explicitly with `--root`',
            'python3 "<zen-cad-root>/scripts/new_milestone.py" --root "<zen-cad-root>" --request "<goal>"',
            '"<zen-cad-root>/zen-cad" --root "<zen-cad-root>" new "<goal>"',
            'Use the last form only when the current command cwd is already the resolved Zen CAD root',
        ]:
            self.assertIn(phrase, text)
        for phrase in [
            'When running inside a Zen CAD repository',
            'from the Zen CAD repository root, internally run',
        ]:
            self.assertNotIn(phrase, text)

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

    def test_agentic_cad_uses_canonical_milestone_paths(self) -> None:
        text = (ROOT / 'skills/agentic-cad/SKILL.md').read_text(encoding='utf-8')
        for phrase in [
            '00_requirements/requirements_brief.md',
            '02_parts/selected_parts_manifest.json',
            '03_cad/custom_cad_handoff.yaml',
            '04_assembly/contact_map.json',
            '05_validation/validation_report.json',
            '06_bom/bom.csv',
            '07_report/final_engineering_report.md',
            'evidence_type: "environment"',
        ]:
            self.assertIn(phrase, text)
        for phrase in [
            '`requirements.md` or `requirements.json`',
            '`CONTACT_MAP.json`',
            '`BOM.csv` or `BOM.json`',
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

    def test_agent_creates_milestone_from_prompt_after_setup(self) -> None:
        searchable_text = '\n'.join(
            path.read_text(encoding='utf-8')
            for path in [
                ROOT / 'README.md',
                ROOT / 'docs/cobra_usage.md',
                ROOT / 'docs/environment_setup.md',
                ROOT / 'prompts/project_kickoff.md',
                ROOT / 'prompts/new_milestone.md',
                ROOT / 'skills/agentic-cad/SKILL.md',
            ]
        ).casefold()
        for phrase in [
            'prompt-first milestone startup',
            'do not ask the user to run',
            'python3 scripts/new_milestone.py --request "<goal>"',
            '기어 박스를 만들고 싶어',
            '003_gearbox',
        ]:
            self.assertIn(phrase.casefold(), searchable_text)
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
            self.assertTrue((work / 'milestones/003_gearbox/milestone.yaml').exists())

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
                    str(skills_root / 'agentic-cad'),
                    '--skip-validation',
                ],
                cwd=work,
                text=True,
                capture_output=True,
                check=True,
            )

            for skill_name in ['agentic-cad', 'cad-artifact-reviewer', 'manufacturing-preflight', 'mechanism-kinematics', 'spec-to-cad', 'self-evolving-producer-verifier', 'source-step-parts']:
                self.assertTrue((skills_root / skill_name / 'SKILL.md').exists(), skill_name)
                context = skills_root / skill_name / 'ZEN_CAD_WORKSPACE.md'
                self.assertTrue(context.exists(), skill_name)
                context_text = context.read_text(encoding='utf-8')
                self.assertIn(f'Repository root: {work.resolve()}', context_text)
                self.assertIn('The CoBrA daemon/session cwd is not the Zen CAD workspace contract.', context_text)
                self.assertIn('python3 "<repository-root>/scripts/new_milestone.py" --root "<repository-root>" --request "<goal>"', context_text)


if __name__ == '__main__':
    unittest.main()
