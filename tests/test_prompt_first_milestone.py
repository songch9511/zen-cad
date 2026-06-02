#!/usr/bin/env python3
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


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
            shutil.copytree(
                ROOT,
                work,
                ignore=shutil.ignore_patterns('.git', 'releases', 'tests', '__pycache__'),
            )
            shutil.rmtree(work / 'milestones/002_setup_smoke_robot_gripper', ignore_errors=True)
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


if __name__ == '__main__':
    unittest.main()
