#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

REQUIRED = [
    'milestone.yaml',
    '00_requirements/requirements_brief.md',
    '01_research/research_log.md',
    '02_parts/part_classification_table.md',
    '02_parts/selected_parts_manifest.json',
    '03_cad/custom_cad_handoff.yaml',
    '04_assembly/contact_map.json',
    '04_assembly/connections.json',
    '05_validation/validation_report.json',
    '06_bom/bom.csv',
    '07_report/final_engineering_report.md',
]

def main() -> int:
    milestone = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    missing = [p for p in REQUIRED if not (milestone / p).exists()]
    errors = []
    if missing:
        errors.extend(f'missing {p}' for p in missing)
    for rel in ['02_parts/selected_parts_manifest.json', '04_assembly/contact_map.json', '04_assembly/connections.json', '05_validation/validation_report.json']:
        try:
            data = json.loads((milestone / rel).read_text(encoding='utf-8'))
        except Exception as exc:
            errors.append(f'{rel}: invalid JSON: {exc}')
            continue
        if not isinstance(data, dict) or not data.get('milestone_id'):
            errors.append(f'{rel}: missing milestone_id')
    if (milestone / '06_bom/bom.csv').exists():
        with (milestone / '06_bom/bom.csv').open(newline='', encoding='utf-8') as f:
            header = next(csv.reader(f))
        if 'part_id' not in header or 'classification' not in header:
            errors.append('06_bom/bom.csv: missing required columns')
    if errors:
        print(f'Milestone validation failed: {milestone}')
        for error in errors:
            print(f'- {error}')
        return 1
    print(f'OK: milestone validates: {milestone}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
