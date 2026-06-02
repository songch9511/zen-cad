#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

JSON_PAIRS = [
    ('schemas/selected_parts_manifest.schema.json', 'templates/selected_parts_manifest.json'),
    ('schemas/contact_map.schema.json', 'templates/contact_map.json'),
    ('schemas/connections.schema.json', 'templates/connections.json'),
    ('schemas/validation_report.schema.json', 'templates/validation_report.json'),
    ('schemas/selected_parts_manifest.schema.json', 'milestones/_template/02_parts/selected_parts_manifest.json'),
    ('schemas/contact_map.schema.json', 'milestones/_template/04_assembly/contact_map.json'),
    ('schemas/connections.schema.json', 'milestones/_template/04_assembly/connections.json'),
    ('schemas/validation_report.schema.json', 'milestones/_template/05_validation/validation_report.json'),
    ('schemas/selected_parts_manifest.schema.json', 'milestones/001_nema17_belt_linear_actuator/02_parts/selected_parts_manifest.json'),
    ('schemas/contact_map.schema.json', 'milestones/001_nema17_belt_linear_actuator/04_assembly/contact_map.json'),
    ('schemas/connections.schema.json', 'milestones/001_nema17_belt_linear_actuator/04_assembly/connections.json'),
    ('schemas/validation_report.schema.json', 'milestones/001_nema17_belt_linear_actuator/05_validation/validation_report.json'),
]

REQUIRED_BY_SCHEMA = {
    'selected_parts_manifest.schema.json': ['milestone_id', 'parts'],
    'contact_map.schema.json': ['milestone_id', 'contacts'],
    'connections.schema.json': ['milestone_id', 'connections'],
    'validation_report.schema.json': ['milestone_id', 'status', 'checks', 'summary'],
}

def validate_required(schema_path: Path, data_path: Path) -> list[str]:
    data = json.loads(data_path.read_text(encoding='utf-8'))
    required = REQUIRED_BY_SCHEMA.get(schema_path.name, [])
    errors = []
    if not isinstance(data, dict):
        errors.append('top-level JSON is not an object')
        return errors
    for key in required:
        if key not in data:
            errors.append(f'missing required key: {key}')
    return errors

def validate_bom(root: Path) -> list[str]:
    expected = json.loads((root / 'schemas/bom.columns.json').read_text(encoding='utf-8'))['columns']
    paths = ['templates/bom.csv', 'milestones/_template/06_bom/bom.csv', 'milestones/001_nema17_belt_linear_actuator/06_bom/bom.csv']
    errors = []
    for rel in paths:
        with (root / rel).open(newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader)
        if header != expected:
            errors.append(f'{rel}: header mismatch {header!r}')
    return errors

def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    errors = []
    for schema_rel, data_rel in JSON_PAIRS:
        schema_path = root / schema_rel
        data_path = root / data_rel
        json.loads(schema_path.read_text(encoding='utf-8'))
        errors.extend(f'{data_rel}: {err}' for err in validate_required(schema_path, data_path))
    errors.extend(validate_bom(root))
    if errors:
        print('Schema validation failed:')
        for error in errors:
            print(f'- {error}')
        return 1
    print(f'OK: {len(JSON_PAIRS)} JSON artifacts and BOM CSV headers validated')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
