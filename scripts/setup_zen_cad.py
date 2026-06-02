#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def run_step(label: str, command: list[str], cwd: Path) -> None:
    print(f'\n==> {label}')
    print('$ ' + ' '.join(command))
    completed = subprocess.run(command, cwd=cwd)
    if completed.returncode != 0:
        raise SystemExit(f'ERROR: {label} failed with exit code {completed.returncode}')


def sync_cobra_skill(root: Path, skill_dir: Path) -> Path:
    source = root / 'skills/agentic-cad/SKILL.md'
    if not source.exists():
        raise SystemExit(f'ERROR: missing embedded /agentic-cad skill: {source}')
    target_dir = skill_dir.expanduser().resolve()
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / 'SKILL.md'
    shutil.copy2(source, target)
    print(f'Synced /agentic-cad skill to: {target}')
    return target


def create_or_reuse_milestone(root: Path, milestone_id: str, title: str) -> Path:
    milestones_dir = (root / 'milestones').resolve()
    target = (milestones_dir / milestone_id).resolve()
    if target.parent != milestones_dir:
        raise SystemExit('ERROR: milestone id must name a direct child under milestones/')
    if target.exists():
        print(f'Milestone already exists, leaving unchanged: {target}')
        return target
    run_step(
        'create milestone',
        [
            sys.executable,
            str(root / 'scripts/new_milestone.py'),
            '--root',
            str(root),
            '--id',
            milestone_id,
            '--title',
            title,
        ],
        root,
    )
    return target


def validate(root: Path, extra_milestone: Path | None) -> None:
    run_step('check required files', [sys.executable, str(root / 'scripts/check_required_files.py'), str(root)], root)
    run_step('check JSON schemas', [sys.executable, str(root / 'scripts/check_json_schemas.py'), str(root)], root)
    run_step('validate milestone template', [sys.executable, str(root / 'scripts/validate_milestone.py'), str(root / 'milestones/_template')], root)
    reference = root / 'milestones/001_nema17_belt_linear_actuator'
    if reference.exists():
        run_step('validate reference milestone', [sys.executable, str(root / 'scripts/validate_milestone.py'), str(reference)], root)
    if extra_milestone is not None:
        run_step('validate requested milestone', [sys.executable, str(root / 'scripts/validate_milestone.py'), str(extra_milestone)], root)


def main() -> int:
    parser = argparse.ArgumentParser(description='One-command Zen CAD setup helper for any milestone-based CAD job.')
    parser.add_argument('--root', default=None, help='Zen CAD repository root. Defaults to this script\'s parent repository.')
    parser.add_argument('--sync-cobra-skill', action='store_true', help='Copy skills/agentic-cad/SKILL.md into a CoBrA skills directory.')
    parser.add_argument('--cobra-skill-dir', default='~/.cobra/workspace/skills/agentic-cad', help='Target directory for CoBrA /agentic-cad skill sync.')
    parser.add_argument('--milestone-id', help='Optional unique lowercase snake_case milestone id, e.g. 002_desktop_cnc_fixture.')
    parser.add_argument('--milestone-title', help='Human-readable title for --milestone-id.')
    parser.add_argument('--skip-validation', action='store_true', help='Skip built-in required-file/schema/milestone validation.')
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve() if args.root else repo_root_from_script()
    if not (root / 'README.md').exists() or not (root / 'scripts/new_milestone.py').exists():
        raise SystemExit(f'ERROR: not a Zen CAD repository root: {root}')

    milestone = None
    if bool(args.milestone_id) != bool(args.milestone_title):
        raise SystemExit('ERROR: use --milestone-id and --milestone-title together')
    if args.sync_cobra_skill:
        sync_cobra_skill(root, Path(args.cobra_skill_dir))
    if args.milestone_id and args.milestone_title:
        milestone = create_or_reuse_milestone(root, args.milestone_id, args.milestone_title)
    if not args.skip_validation:
        validate(root, milestone)

    print('\nZen CAD setup complete.')
    print(f'Repository root: {root}')
    if milestone is not None:
        print(f'Milestone ready: {milestone}')
    print('Next: open prompts/new_milestone.md and skills/agentic-cad/SKILL.md in your agentic CAD environment.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
