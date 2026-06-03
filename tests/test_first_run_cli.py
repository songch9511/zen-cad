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
            self.assertIn('[WARN] CoBrA skill discovery', completed.stdout)
            self.assertIn('CAD toolchain preflight', completed.stdout)
            self.assertIn('does not change CoBrA process cwd by itself', completed.stdout)
            self.assertIn('Do not treat the Zen CAD repo as the CoBrA daemon cwd', completed.stdout)
            self.assertNotIn('Start CoBrA from this repo', completed.stdout)
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
            self.assertIn('Do not treat the Zen CAD repo as the CoBrA daemon cwd', completed.stdout)
            self.assertNotIn('Start CoBrA from this repo', completed.stdout)
            for skill_name in ['agentic-cad', 'cad-artifact-reviewer', 'manufacturing-preflight', 'mechanism-kinematics', 'spec-to-cad', 'self-evolving-producer-verifier', 'source-step-parts']:
                self.assertTrue((skills_root / skill_name / 'SKILL.md').exists(), skill_name)
                context = skills_root / skill_name / 'ZEN_CAD_WORKSPACE.md'
                self.assertTrue(context.exists(), skill_name)
                context_text = context.read_text(encoding='utf-8')
                self.assertIn(f'Repository root: {work.resolve()}', context_text)
                self.assertIn('The CoBrA daemon/session cwd is not the Zen CAD workspace contract.', context_text)
                self.assertIn('python3 "<repository-root>/scripts/new_milestone.py" --root "<repository-root>" --request "<goal>"', context_text)

            doctor = run_cli(work, 'doctor', '--cobra-skills-root', str(skills_root))
            self.assertEqual(doctor.returncode, 0, doctor.stderr + doctor.stdout)
            self.assertIn('installed, fresh, and bound to', doctor.stdout)

    def test_doctor_warns_when_cobra_skill_binding_is_missing(self) -> None:
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
            (skills_root / 'agentic-cad' / 'ZEN_CAD_WORKSPACE.md').unlink()

            doctor = run_cli(work, 'doctor', '--cobra-skills-root', str(skills_root))

            self.assertEqual(doctor.returncode, 0, doctor.stderr + doctor.stdout)
            self.assertIn('[WARN] CoBrA workspace binding', doctor.stdout)
            self.assertIn('missing ZEN_CAD_WORKSPACE.md for agentic-cad', doctor.stdout)

    def test_doctor_accepts_build123d_ocp_python_backend(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / 'zen-cad-kit'
            copy_repo_fixture(work)
            fake_python = Path(tmp) / 'fake-python'
            fake_python.write_text(
                '#!/bin/sh\n'
                'cat <<\'JSON\'\n'
                '{"ok": true, "executable": "fake-python", "version": "3.11.0", "in_virtualenv": true, '
                '"modules": {"numpy": true, "trimesh": true, "build123d": true, "cadquery": false, "OCP": true}, '
                '"openscad": null, "stl_round_trip": true, "build123d_step_smoke": true}\n'
                'JSON\n',
                encoding='utf-8',
            )
            fake_python.chmod(0o755)

            completed = run_cli(
                work,
                'doctor',
                '--cad-required',
                '--python',
                str(fake_python),
                '--cobra-skills-root',
                str(Path(tmp) / 'cobra-skills'),
            )

            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertIn('[PASS] build123d import', completed.stdout)
            self.assertIn('[PASS] OCP import', completed.stdout)
            self.assertIn('[PASS] build123d STEP/OCP smoke', completed.stdout)
            self.assertIn('[PASS] CAD kernel/export path', completed.stdout)

    def test_new_command_creates_milestone_and_prints_next_steps(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / 'zen-cad-kit'
            copy_repo_fixture(work)

            completed = run_cli(work, 'new', '기어 박스를 만들고 싶어')

            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertIn('Milestone creation: PASS', completed.stdout)
            self.assertIn('Active milestone: milestones/003_gearbox', completed.stdout)
            self.assertIn('Continue with /agentic-cad', completed.stdout)
            self.assertTrue((work / 'milestones/003_gearbox/milestone.yaml').exists())

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

    def test_validation_levels_are_separate_gates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / 'zen-cad-kit'
            copy_repo_fixture(work)

            structure = run_cli(work, 'validate', '--level', 'structure', 'milestones/001_nema17_belt_linear_actuator')
            self.assertEqual(structure.returncode, 0, structure.stderr + structure.stdout)
            self.assertIn('Zen CAD validation result: PASS', structure.stdout)
            self.assertNotIn('Completion evidence:', structure.stdout)

            completion = run_cli(work, 'validate', '--level', 'completion', 'milestones/001_nema17_belt_linear_actuator')
            self.assertEqual(completion.returncode, 2, completion.stderr + completion.stdout)
            self.assertIn('Zen CAD completion validation result: BLOCKED', completion.stdout)
            self.assertIn('Blocking gates:', completion.stdout)
            self.assertIn('Gate 2 standard part source-lock', completion.stdout)
            self.assertIn('Gate 6 CAD-kernel validation', completion.stdout)

            alias = run_cli(work, 'validate-completion', 'milestones/001_nema17_belt_linear_actuator')
            self.assertEqual(alias.returncode, 2, alias.stderr + alias.stdout)

            demo = run_cli(work, 'validate-completion', 'milestones/002_nema17_mount_plate')
            self.assertEqual(demo.returncode, 0, demo.stderr + demo.stdout)
            self.assertIn('Zen CAD completion validation result: PASS', demo.stdout)

    def test_completion_blocks_pass_report_without_command_argv(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / 'zen-cad-kit'
            copy_repo_fixture(work)
            report = work / 'milestones/002_nema17_mount_plate/05_validation/validation_report.json'
            data = json.loads(report.read_text(encoding='utf-8'))
            data['checks'][1]['command']['argv'] = []
            report.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')

            completed = run_cli(work, 'validate-completion', 'milestones/002_nema17_mount_plate')

            self.assertEqual(completed.returncode, 2, completed.stderr + completed.stdout)
            self.assertIn('Gate 6 CAD-kernel validation', completed.stdout)
            self.assertIn('command.argv must be a non-empty string array', completed.stdout)

    def test_completion_blocks_artifact_hash_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / 'zen-cad-kit'
            copy_repo_fixture(work)
            report = work / 'milestones/002_nema17_mount_plate/05_validation/validation_report.json'
            data = json.loads(report.read_text(encoding='utf-8'))
            data['checks'][1]['artifacts'][1]['sha256'] = '0' * 64
            report.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')

            completed = run_cli(work, 'validate-completion', 'milestones/002_nema17_mount_plate')

            self.assertEqual(completed.returncode, 2, completed.stderr + completed.stdout)
            self.assertIn('Gate 6 CAD-kernel validation', completed.stdout)
            self.assertIn('sha256 mismatch', completed.stdout)

    def test_completion_blocks_assembly_rows_without_geometry_evidence_links(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / 'zen-cad-kit'
            copy_repo_fixture(work)
            contact_map = work / 'milestones/002_nema17_mount_plate/04_assembly/contact_map.json'
            data = json.loads(contact_map.read_text(encoding='utf-8'))
            data['contacts'][0].pop('evidence_check_ids')
            contact_map.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')

            completed = run_cli(work, 'validate-completion', 'milestones/002_nema17_mount_plate')

            self.assertEqual(completed.returncode, 2, completed.stderr + completed.stdout)
            self.assertIn('Gate 4 assembly contract', completed.stdout)
            self.assertIn('has no evidence_check_ids', completed.stdout)

    def test_completion_requires_geometry_inspection_evidence_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / 'zen-cad-kit'
            copy_repo_fixture(work)
            report = work / 'milestones/002_nema17_mount_plate/05_validation/validation_report.json'
            data = json.loads(report.read_text(encoding='utf-8'))
            data['checks'][3]['evidence_type'] = 'other'
            report.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')

            completed = run_cli(work, 'validate-completion', 'milestones/002_nema17_mount_plate')

            self.assertEqual(completed.returncode, 2, completed.stderr + completed.stdout)
            self.assertIn('Gate 6 CAD-kernel validation', completed.stdout)
            self.assertIn('missing required completion evidence types: geometry_inspection', completed.stdout)

    def test_completion_requires_environment_evidence_when_cad_preflight_is_blocked(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / 'zen-cad-kit'
            copy_repo_fixture(work)
            fake_python = Path(tmp) / 'fake-python'
            fake_python.write_text(
                '#!/bin/sh\n'
                'cat <<\'JSON\'\n'
                '{"ok": true, "executable": "fake-python", "version": "3.11.0", "in_virtualenv": true, '
                '"modules": {"numpy": false, "trimesh": false, "build123d": false, "cadquery": false, "OCP": false}, '
                '"openscad": null, "stl_round_trip": false, "build123d_step_smoke": false}\n'
                'JSON\n',
                encoding='utf-8',
            )
            fake_python.chmod(0o755)
            report = work / 'milestones/002_nema17_mount_plate/05_validation/validation_report.json'
            data = json.loads(report.read_text(encoding='utf-8'))
            data['checks'][6]['evidence_type'] = 'other'
            report.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')

            completed = run_cli(
                work,
                'validate-completion',
                '--python',
                str(fake_python),
                'milestones/002_nema17_mount_plate',
            )

            self.assertEqual(completed.returncode, 2, completed.stderr + completed.stdout)
            self.assertIn('Gate 0 doctor / environment preflight', completed.stdout)
            self.assertIn('validation_report has no environment evidence check', completed.stdout)

    def test_source_lock_blocks_proxies_and_unlocked_standard_parts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / 'zen-cad-kit'
            copy_repo_fixture(work)

            completed = run_cli(work, 'source-lock', 'milestones/001_nema17_belt_linear_actuator')

            self.assertEqual(completed.returncode, 2, completed.stderr + completed.stdout)
            self.assertIn('Source-lock: BLOCKED', completed.stdout)
            self.assertIn('completion_eligible: false', completed.stdout)
            self.assertIn('proxy_only artifacts are completion-ineligible', completed.stdout)
            self.assertIn('status is', completed.stdout)

            concept = run_cli(work, 'source-lock', '--maturity', 'concept', 'milestones/001_nema17_belt_linear_actuator')
            self.assertEqual(concept.returncode, 0, concept.stderr + concept.stdout)
            self.assertIn('Source-lock: WARN', concept.stdout)

            demo = run_cli(work, 'source-lock', 'milestones/002_nema17_mount_plate')
            self.assertEqual(demo.returncode, 0, demo.stderr + demo.stdout)
            self.assertIn('status: generated_custom', demo.stdout)

    def test_blocked_report_writes_truthful_blocked_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp) / 'zen-cad-kit'
            copy_repo_fixture(work)

            completed = run_cli(work, 'blocked-report', '--write', 'milestones/001_nema17_belt_linear_actuator')

            self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
            self.assertIn('Verdict: BLOCKED', completed.stdout)
            report = work / 'milestones/001_nema17_belt_linear_actuator/07_report/blocked_report.md'
            self.assertTrue(report.exists())
            text = report.read_text(encoding='utf-8')
            self.assertIn('Structure PASS is not completion PASS.', text)
            self.assertIn('Gate 2 standard part source-lock', text)

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
