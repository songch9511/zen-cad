#!/usr/bin/env python3
from __future__ import annotations

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
        ignore=shutil.ignore_patterns('.git', 'releases', 'tests', '__pycache__'),
    )


def run_cli(work: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, 'scripts/zen_cad.py', *args],
        cwd=work,
        text=True,
        capture_output=True,
    )


class FirstRunCliTest(unittest.TestCase):
    def test_doctor_reports_pass_and_cobra_workspace_note(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / 'zen-cad-kit'
            copy_repo_fixture(work)

            completed = run_cli(work, 'doctor', '--cobra-skills-root', str(Path(tmp) / 'cobra-skills'))

            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertIn('Zen CAD doctor: PASS', completed.stdout)
            self.assertIn('[WARN] CoBrA skill sync', completed.stdout)
            self.assertIn('does not register this repository as the active CoBrA workspace', completed.stdout)
            self.assertIn('In CoBrA/Codex/Claude Code/Cursor, ask:', completed.stdout)
            self.assertIn('Manual terminal fallback:', completed.stdout)

    def test_init_with_cobra_syncs_companion_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / 'zen-cad-kit'
            skills_root = Path(tmp) / 'cobra-skills'
            copy_repo_fixture(work)

            completed = run_cli(
                work,
                'init',
                '--with-cobra',
                '--cobra-skills-root',
                str(skills_root),
                '--skip-validation',
            )

            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertIn('Zen CAD init: PASS', completed.stdout)
            self.assertIn('CoBrA skill sync: PASS', completed.stdout)
            for skill_name in ['agentic-cad', 'spec-to-cad', 'self-evolving-producer-verifier']:
                self.assertTrue((skills_root / skill_name / 'SKILL.md').exists(), skill_name)

    def test_new_command_creates_milestone_and_prints_next_steps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / 'zen-cad-kit'
            copy_repo_fixture(work)

            completed = run_cli(work, 'new', '기어 박스를 만들고 싶어')

            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertIn('Milestone creation: PASS', completed.stdout)
            self.assertIn('Active milestone: milestones/002_gearbox', completed.stdout)
            self.assertIn('Continue with /agentic-cad', completed.stdout)
            self.assertTrue((work / 'milestones/002_gearbox/milestone.yaml').exists())

    def test_validate_splits_structure_pass_from_completion_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / 'zen-cad-kit'
            copy_repo_fixture(work)

            completed = run_cli(work, 'validate', 'milestones/001_nema17_belt_linear_actuator')

            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertIn('Zen CAD validation result: PASS', completed.stdout)
            self.assertIn('Completion evidence: BLOCKED', completed.stdout)
            self.assertIn('validation_report status is', completed.stdout)

            strict = run_cli(
                work,
                'validate',
                'milestones/001_nema17_belt_linear_actuator',
                '--completion-required',
            )
            self.assertEqual(strict.returncode, 2, strict.stderr + strict.stdout)

    def test_default_validate_does_not_report_template_as_active_milestone(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / 'zen-cad-kit'
            copy_repo_fixture(work)

            completed = run_cli(work, 'validate')

            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertIn('Milestone: 001_nema17_belt_linear_actuator', completed.stdout)
            self.assertNotIn('Milestone: _template', completed.stdout)

    def test_subcommand_root_argument_can_point_to_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / 'zen-cad-kit'
            outside = Path(tmp) / 'outside'
            outside.mkdir()
            copy_repo_fixture(work)

            completed = subprocess.run(
                [sys.executable, str(work / 'scripts/zen_cad.py'), 'doctor', '--root', str(work)],
                cwd=outside,
                text=True,
                capture_output=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertIn('Zen CAD doctor: PASS', completed.stdout)


if __name__ == '__main__':
    unittest.main()
