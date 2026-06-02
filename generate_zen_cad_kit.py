#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def repo_root_from_script() -> Path:
    return Path(__file__).resolve().parent


def run_step(label: str, command: list[str], cwd: Path) -> None:
    print(f'\n==> {label}')
    print('$ ' + ' '.join(command))
    completed = subprocess.run(command, cwd=cwd, text=True)
    if completed.returncode != 0:
        raise SystemExit(f'ERROR: {label} failed with exit code {completed.returncode}')


def sync_skill(source: Path, root: Path) -> Path:
    if not source.exists():
        raise SystemExit(f'ERROR: source skill does not exist: {source}')
    target = root / 'skills/agentic-cad/SKILL.md'
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    print(f'Synced /agentic-cad skill from {source} to {target}')
    return target


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Developer helper that validates the current Zen CAD tree and refreshes the versioned release package.'
    )
    parser.add_argument('--root', default=None, help='Zen CAD repository root. Defaults to this script directory.')
    parser.add_argument(
        '--sync-skill-from',
        help='Optional path to a SKILL.md file to copy into skills/agentic-cad/SKILL.md before validation.',
    )
    parser.add_argument('--skip-validation', action='store_true', help='Refresh the release package without running setup validation.')
    args = parser.parse_args()

    root = Path(args.root).expanduser().resolve() if args.root else repo_root_from_script()
    if not (root / 'scripts/setup_zen_cad.py').exists() or not (root / 'scripts/export_release_package.py').exists():
        raise SystemExit(f'ERROR: not a Zen CAD repository root: {root}')

    if args.sync_skill_from:
        sync_skill(Path(args.sync_skill_from).expanduser().resolve(), root)

    if not args.skip_validation:
        run_step('validate Zen CAD kit', [sys.executable, str(root / 'scripts/setup_zen_cad.py'), '--root', str(root)], root)
    run_step('export release package', [sys.executable, str(root / 'scripts/export_release_package.py'), str(root)], root)

    print('\nZen CAD kit refresh complete.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
