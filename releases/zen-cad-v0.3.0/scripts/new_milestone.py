#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
from datetime import date
from pathlib import Path

def main() -> int:
    parser = argparse.ArgumentParser(description='Create a new Zen CAD milestone from the template.')
    parser.add_argument('--id', required=True, help='Milestone id, e.g. 002_robot_gripper')
    parser.add_argument('--title', required=True, help='Human-readable milestone title')
    parser.add_argument('--root', default='.', help='Zen CAD repository root')
    args = parser.parse_args()

    root = Path(args.root).resolve()
    template = root / 'milestones/_template'
    target = root / f'milestones/{args.id}'
    if target.exists():
        raise SystemExit(f'ERROR: milestone already exists: {target}')
    shutil.copytree(template, target)
    milestone_file = target / 'milestone.yaml'
    text = milestone_file.read_text(encoding='utf-8')
    text = text.replace('REPLACE_WITH_MILESTONE_ID', args.id).replace('REPLACE_WITH_TITLE', args.title).replace('REPLACE_WITH_DATE', date.today().isoformat())
    milestone_file.write_text(text, encoding='utf-8')
    for rel in ['02_parts/selected_parts_manifest.json', '04_assembly/contact_map.json', '04_assembly/connections.json', '05_validation/validation_report.json']:
        path = target / rel
        path.write_text(path.read_text(encoding='utf-8').replace('REPLACE_WITH_MILESTONE_ID', args.id), encoding='utf-8')
    print(f'Created milestone: {target}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
