#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT_JSON_PAIRS = [
    ('schemas/bom.schema.json', 'schemas/bom.columns.json'),
    ('schemas/selected_parts_manifest.schema.json', 'templates/selected_parts_manifest.json'),
    ('schemas/contact_map.schema.json', 'templates/contact_map.json'),
    ('schemas/connections.schema.json', 'templates/connections.json'),
    ('schemas/validation_report.schema.json', 'templates/validation_report.json'),
]

MILESTONE_JSON_PAIRS = [
    ('schemas/selected_parts_manifest.schema.json', '02_parts/selected_parts_manifest.json'),
    ('schemas/contact_map.schema.json', '04_assembly/contact_map.json'),
    ('schemas/connections.schema.json', '04_assembly/connections.json'),
    ('schemas/validation_report.schema.json', '05_validation/validation_report.json'),
]


def iter_milestone_dirs(root: Path) -> list[Path]:
    milestones_dir = root / 'milestones'
    if not milestones_dir.exists():
        return []
    return sorted(
        (child for child in milestones_dir.iterdir() if child.is_dir() and (child / 'milestone.yaml').exists()),
        key=lambda path: path.name,
    )


def type_name(value: object) -> str:
    if isinstance(value, bool):
        return 'boolean'
    if isinstance(value, dict):
        return 'object'
    if isinstance(value, list):
        return 'array'
    if isinstance(value, str):
        return 'string'
    if isinstance(value, int):
        return 'integer'
    if isinstance(value, float):
        return 'number'
    if value is None:
        return 'null'
    return type(value).__name__


def matches_type(value: object, expected: str) -> bool:
    if expected == 'object':
        return isinstance(value, dict)
    if expected == 'array':
        return isinstance(value, list)
    if expected == 'string':
        return isinstance(value, str)
    if expected == 'boolean':
        return isinstance(value, bool)
    if expected == 'integer':
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == 'number':
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == 'null':
        return value is None
    return True


def validate_schema(schema: dict[str, object], data: object, path: str = '$') -> list[str]:
    errors: list[str] = []
    enum_values = schema.get('enum')
    if isinstance(enum_values, list) and data not in enum_values:
        return [f'{path}: expected one of {enum_values!r}, got {data!r}']

    expected_type = schema.get('type')
    if isinstance(expected_type, str) and not matches_type(data, expected_type):
        return [f'{path}: expected {expected_type}, got {type_name(data)}']

    if isinstance(data, str):
        min_length = schema.get('minLength')
        if isinstance(min_length, int) and len(data) < min_length:
            errors.append(f'{path}: expected length >= {min_length}')

    if isinstance(data, dict):
        required = schema.get('required')
        if isinstance(required, list):
            for key in required:
                if isinstance(key, str) and key not in data:
                    errors.append(f'{path}: missing required key: {key}')

        properties = schema.get('properties')
        if isinstance(properties, dict):
            additional = schema.get('additionalProperties', True)
            if additional is False:
                for key in sorted(set(data) - set(properties)):
                    errors.append(f'{path}: additional property not allowed: {key}')
            for key, child_schema in properties.items():
                if isinstance(key, str) and key in data and isinstance(child_schema, dict):
                    errors.extend(validate_schema(child_schema, data[key], f'{path}.{key}'))

    if isinstance(data, list):
        item_schema = schema.get('items')
        if isinstance(item_schema, dict):
            for index, item in enumerate(data):
                errors.extend(validate_schema(item_schema, item, f'{path}[{index}]'))

    return errors


def read_json(path: Path) -> tuple[object | None, list[str]]:
    try:
        return json.loads(path.read_text(encoding='utf-8')), []
    except Exception as exc:
        return None, [f'{path}: invalid JSON: {exc}']


def validate_json_artifact(schema_path: Path, data_path: Path) -> list[str]:
    schema, schema_errors = read_json(schema_path)
    data, data_errors = read_json(data_path)
    errors = schema_errors + data_errors
    if errors:
        return errors
    if not isinstance(schema, dict):
        return [f'{schema_path}: schema top-level JSON is not an object']
    return [f'{data_path}: {error}' for error in validate_schema(schema, data)]


def json_artifact_pairs(root: Path) -> list[tuple[Path, Path]]:
    pairs = [(root / schema_rel, root / data_rel) for schema_rel, data_rel in ROOT_JSON_PAIRS]
    for milestone in iter_milestone_dirs(root):
        pairs.extend((root / schema_rel, milestone / data_rel) for schema_rel, data_rel in MILESTONE_JSON_PAIRS)
    return pairs


def validate_bom(root: Path, milestone_dirs: list[Path]) -> tuple[list[str], int]:
    bom_columns, bom_column_errors = read_json(root / 'schemas/bom.columns.json')
    if bom_column_errors:
        return bom_column_errors, 0
    if not isinstance(bom_columns, dict) or not isinstance(bom_columns.get('columns'), list):
        return [f'{root / "schemas/bom.columns.json"}: missing columns list'], 0
    expected = bom_columns['columns']
    paths = [root / 'templates/bom.csv', *(milestone / '06_bom/bom.csv' for milestone in milestone_dirs)]
    errors = []
    for path in paths:
        try:
            with path.open(newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)
        except Exception as exc:
            errors.append(f'{path}: invalid BOM CSV: {exc}')
            continue
        if header != expected:
            errors.append(f'{path}: header mismatch {header!r}')
    return errors, len(paths)


def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    errors = []
    milestone_dirs = iter_milestone_dirs(root)
    json_pairs = json_artifact_pairs(root)
    for schema_path, data_path in json_pairs:
        errors.extend(validate_json_artifact(schema_path, data_path))
    bom_errors, bom_count = validate_bom(root, milestone_dirs)
    errors.extend(bom_errors)
    if errors:
        print('Schema validation failed:')
        for error in errors:
            print(f'- {error}')
        return 1
    print(f'OK: {len(json_pairs)} JSON artifacts and {bom_count} BOM CSV headers validated')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
