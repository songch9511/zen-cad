#!/usr/bin/env python3
from __future__ import annotations

import shutil
import sys
from pathlib import Path

IGNORED_RELEASE_PATTERNS = shutil.ignore_patterns(
    '.DS_Store',
    '__pycache__',
    '*.pyc',
    '.pytest_cache',
)


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    version = (root / 'VERSION').read_text(encoding='utf-8').strip()
    out = root / 'releases' / f'zen-cad-v{version}'
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)
    for name in ['README.md', 'VERSION', 'CHANGELOG.md', 'zen-cad', 'docs', 'skills', 'plugins', 'packages', 'prompts', 'templates', 'schemas', 'checklists', 'scripts', 'milestones/_template', 'milestones/001_nema17_belt_linear_actuator', 'milestones/002_nema17_mount_plate']:
        src = root / name
        dst = out / name
        if src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst, ignore=IGNORED_RELEASE_PATTERNS)
        elif src.exists():
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    print(f'Exported release package: {out}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
