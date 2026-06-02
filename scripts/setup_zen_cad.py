#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parents[1]


def run_step(label: str, command: list[str], cwd: Path, capture: bool = False) -> subprocess.CompletedProcess[str]:
    print(f'\n==> {label}')
    print('$ ' + ' '.join(command))
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=capture)
    if capture:
        if completed.stdout:
            print(completed.stdout, end='')
        if completed.stderr:
            print(completed.stderr, end='', file=sys.stderr)
    if completed.returncode != 0:
        raise SystemExit(f'ERROR: {label} failed with exit code {completed.returncode}')
    return completed


def sync_cobra_skills(root: Path, agentic_cad_dir: Path) -> list[Path]:
    skills_root = agentic_cad_dir.expanduser().resolve().parent
    synced = []
    for source_dir in sorted((root / 'skills').iterdir(), key=lambda path: path.name):
        source = source_dir / 'SKILL.md'
        if not source.exists():
            continue
        target_dir = skills_root / source_dir.name
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / 'SKILL.md'
        shutil.copy2(source, target)
        synced.append(target)
        print(f'Synced /{source_dir.name} skill to: {target}')
    if not synced:
        raise SystemExit(f'ERROR: missing bundled skills under {root / "skills"}')
    return synced


def create_or_reuse_milestone(root: Path, milestone_id: str, title: str, maturity: str) -> Path:
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
            '--maturity',
            maturity,
        ],
        root,
    )
    return target


def create_milestone_from_request(root: Path, request: str, maturity: str) -> Path:
    completed = run_step(
        'create milestone from request',
        [
            sys.executable,
            str(root / 'scripts/new_milestone.py'),
            '--root',
            str(root),
            '--request',
            request,
            '--maturity',
            maturity,
        ],
        root,
        capture=True,
    )
    for line in completed.stdout.splitlines():
        if line.startswith('Created milestone: '):
            return Path(line.removeprefix('Created milestone: ')).resolve()
    raise SystemExit('ERROR: milestone creation did not report a created path')


def iter_milestone_dirs(root: Path) -> list[Path]:
    milestones_dir = root / 'milestones'
    if not milestones_dir.exists():
        return []
    return sorted(
        (child for child in milestones_dir.iterdir() if child.is_dir() and (child / 'milestone.yaml').exists()),
        key=lambda path: path.name,
    )


def validate(root: Path, extra_milestone: Path | None) -> None:
    run_step('check required files', [sys.executable, str(root / 'scripts/check_required_files.py'), str(root)], root)
    run_step('check JSON schemas', [sys.executable, str(root / 'scripts/check_json_schemas.py'), str(root)], root)
    seen = set()
    for milestone in iter_milestone_dirs(root):
        seen.add(milestone.resolve())
        run_step(f'validate milestone {milestone.name}', [sys.executable, str(root / 'scripts/validate_milestone.py'), str(milestone)], root)
    if extra_milestone is not None and extra_milestone.resolve() not in seen:
        run_step(f'validate milestone {extra_milestone.name}', [sys.executable, str(root / 'scripts/validate_milestone.py'), str(extra_milestone)], root)


def main() -> int:
    parser = argparse.ArgumentParser(description='One-command Zen CAD setup helper for any milestone-based CAD job.')
    parser.add_argument('--root', default=None, help='Zen CAD repository root. Defaults to this script\'s parent repository.')
    parser.add_argument('--sync-cobra-skill', action='store_true', help='Copy bundled Zen CAD skills into a CoBrA skills directory.')
    parser.add_argument('--cobra-skill-dir', default='~/.cobra/workspace/skills/agentic-cad', help='Target directory for CoBrA /agentic-cad skill sync. Companion skills sync to sibling directories.')
    parser.add_argument('--milestone-id', help='Optional explicit lowercase snake_case milestone id, e.g. 002_gearbox.')
    parser.add_argument('--milestone-title', help='Human-readable title for --milestone-id.')
    parser.add_argument('--milestone-request', help='Optional natural-language first CAD request; derives milestone id/title automatically, e.g. "기어 박스를 만들고 싶어".')
    parser.add_argument('--maturity', choices=['concept', 'layout', 'final'], default='concept', help='Initial maturity for a created milestone. Defaults to concept.')
    parser.add_argument('--skip-validation', action='store_true', help='Skip built-in required-file/schema/milestone validation.')
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve() if args.root else repo_root_from_script()
    if not (root / 'README.md').exists() or not (root / 'scripts/new_milestone.py').exists():
        raise SystemExit(f'ERROR: not a Zen CAD repository root: {root}')

    milestone = None
    if args.milestone_request and (args.milestone_id or args.milestone_title):
        raise SystemExit('ERROR: use either --milestone-request or --milestone-id/--milestone-title, not both')
    if bool(args.milestone_id) != bool(args.milestone_title):
        raise SystemExit('ERROR: use --milestone-id and --milestone-title together')
    if args.sync_cobra_skill:
        sync_cobra_skills(root, Path(args.cobra_skill_dir))
    if args.milestone_request:
        milestone = create_milestone_from_request(root, args.milestone_request, args.maturity)
    elif args.milestone_id and args.milestone_title:
        milestone = create_or_reuse_milestone(root, args.milestone_id, args.milestone_title, args.maturity)
    if not args.skip_validation:
        validate(root, milestone)

    print('\nZen CAD setup complete.')
    print(f'Repository root: {root}')
    if milestone is not None:
        print(f'Milestone ready: {milestone}')
    print('Next: tell your agent what you want to design, or open prompts/new_milestone.md and skills/agentic-cad/SKILL.md.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
