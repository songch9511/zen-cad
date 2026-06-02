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
            '002_gearbox',
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
            self.assertIn('Milestone id: 002_gearbox', completed.stdout)
            self.assertIn('Title: Gearbox', completed.stdout)
            self.assertTrue((work / 'milestones/002_gearbox/milestone.yaml').exists())

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

            for skill_name in ['agentic-cad', 'spec-to-cad', 'self-evolving-producer-verifier']:
                self.assertTrue((skills_root / skill_name / 'SKILL.md').exists(), skill_name)


if __name__ == '__main__':
    unittest.main()
