#!/usr/bin/env python3
from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path


COMPANION_SKILLS = [
    'agentic-cad',
    'spec-to-cad',
    'self-evolving-producer-verifier',
]

MILESTONE_ARTIFACTS = [
    ('Requirements brief', '00_requirements/requirements_brief.md'),
    ('Research log', '01_research/research_log.md'),
    ('Part classification', '02_parts/part_classification_table.md'),
    ('Selected parts manifest', '02_parts/selected_parts_manifest.json'),
    ('Custom CAD handoff', '03_cad/custom_cad_handoff.yaml'),
    ('CONTACT_MAP', '04_assembly/contact_map.json'),
    ('CONNECTIONS', '04_assembly/connections.json'),
    ('Validation JSON', '05_validation/validation_report.json'),
    ('BOM', '06_bom/bom.csv'),
    ('Final report', '07_report/final_engineering_report.md'),
]


@dataclass
class CheckResult:
    name: str
    status: str
    detail: str = ''


@dataclass
class GateResult:
    gate_id: str
    name: str
    status: str
    detail: str
    smallest_unblock_steps: list[str]


@dataclass
class PartAudit:
    part_id: str
    name: str
    classification: str
    status: str
    completion_eligible: bool
    blockers: list[str]
    smallest_unblock_steps: list[str]


def print_section(title: str) -> None:
    print(f'\n{title}')


def print_check(result: CheckResult) -> None:
    suffix = f' - {result.detail}' if result.detail else ''
    print(f'[{result.status}] {result.name}{suffix}')


def find_repo_root(start: Path, explicit: str | None = None) -> Path:
    if explicit:
        root = Path(explicit).expanduser().resolve()
        if is_repo_root(root):
            return root
        raise SystemExit(f'ERROR: not a Zen CAD repository root: {root}')

    current = start.resolve()
    for candidate in [current, *current.parents]:
        if is_repo_root(candidate):
            return candidate
    raise SystemExit(
        'ERROR: could not find a Zen CAD repository root. '
        'Run this command from zen-cad or pass --root /path/to/zen-cad.'
    )


def is_repo_root(path: Path) -> bool:
    return (
        (path / 'README.md').exists()
        and (path / 'scripts/new_milestone.py').exists()
        and (path / 'skills/agentic-cad/SKILL.md').exists()
    )


def default_cobra_skills_root() -> Path:
    if os.environ.get('COBRA_SKILLS_ROOT'):
        return Path(os.environ['COBRA_SKILLS_ROOT']).expanduser()
    if os.environ.get('COBRA_WORKSPACE'):
        return Path(os.environ['COBRA_WORKSPACE']).expanduser() / 'skills'
    return Path('~/.cobra/workspace/skills').expanduser()


def run_python(root: Path, script: str, args: list[str] | None = None) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(root / script), *(args or [])]
    return subprocess.run(command, cwd=root, text=True, capture_output=True)


def print_command_output(completed: subprocess.CompletedProcess[str]) -> None:
    if completed.stdout:
        print(completed.stdout, end='')
    if completed.stderr:
        print(completed.stderr, end='', file=sys.stderr)


def run_required_file_check(root: Path) -> CheckResult:
    completed = run_python(root, 'scripts/check_required_files.py', [str(root)])
    if completed.returncode == 0:
        return CheckResult('Required files', 'PASS', first_line(completed.stdout))
    return CheckResult('Required files', 'BLOCKED', first_line(completed.stdout or completed.stderr))


def run_schema_check(root: Path) -> CheckResult:
    completed = run_python(root, 'scripts/check_json_schemas.py', [str(root)])
    if completed.returncode == 0:
        return CheckResult('JSON schemas and BOM headers', 'PASS', first_line(completed.stdout))
    return CheckResult('JSON schemas and BOM headers', 'BLOCKED', first_line(completed.stdout or completed.stderr))


def first_line(text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return ''


def is_meaningful(value: object) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        normalized = value.strip()
        return bool(normalized) and normalized.casefold() not in {'tbd', 'none', 'null', 'n/a', 'na', 'unknown'}
    return True


def has_importable_module(module_name: str) -> bool:
    return importlib.util.find_spec(module_name) is not None


def local_artifact_exists(milestone: Path, value: object) -> bool:
    if not is_meaningful(value) or not isinstance(value, str):
        return False
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = milestone / path
    return path.exists() and path.stat().st_size > 0


def value_from_any(data: dict[str, object], *keys: str) -> object:
    for key in keys:
        value = data.get(key)
        if is_meaningful(value):
            return value
    return None


def read_json_file(path: Path) -> tuple[dict[str, object] | None, str]:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except Exception as exc:
        return None, str(exc)
    if not isinstance(data, dict):
        return None, 'top-level JSON is not an object'
    return data, ''


def check_writable_directory(path: Path) -> bool:
    try:
        path.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(prefix='.zen-cad-doctor-', dir=path, delete=True):
            pass
    except Exception:
        return False
    return True


def sample_stl_round_trip_passes() -> bool:
    if not has_importable_module('trimesh'):
        return False
    try:
        trimesh = importlib.import_module('trimesh')
        stl_text = """solid sample
facet normal 0 0 1
  outer loop
    vertex 0 0 0
    vertex 1 0 0
    vertex 0 1 0
  endloop
endfacet
endsolid sample
"""
        with tempfile.NamedTemporaryFile('w', suffix='.stl', encoding='utf-8') as file:
            file.write(stl_text)
            file.flush()
            mesh = trimesh.load(file.name, force='mesh')
        return len(getattr(mesh, 'vertices', [])) > 0 and len(getattr(mesh, 'faces', [])) > 0
    except Exception:
        return False


def cad_toolchain_checks(root: Path) -> list[CheckResult]:
    in_virtualenv = sys.prefix != getattr(sys, 'base_prefix', sys.prefix)
    cadquery_ready = has_importable_module('cadquery')
    openscad_ready = shutil.which('openscad') is not None
    stl_round_trip = sample_stl_round_trip_passes()
    checks = [
        CheckResult('Python runtime', 'PASS' if sys.version_info >= (3, 10) else 'WARN', f'Python {sys.version.split()[0]}; Python 3.10+ recommended'),
        CheckResult('Python virtualenv', 'PASS' if in_virtualenv else 'WARN', 'active virtualenv' if in_virtualenv else 'not running inside a virtualenv'),
        CheckResult('numpy import', 'PASS' if has_importable_module('numpy') else 'ENV_BLOCKED', 'required for many CAD/mesh validation flows'),
        CheckResult('trimesh import', 'PASS' if has_importable_module('trimesh') else 'ENV_BLOCKED', 'required for STL/mesh loadability checks'),
        CheckResult('cadquery import', 'PASS' if cadquery_ready else 'ENV_BLOCKED', 'required unless another kernel path is used'),
        CheckResult('OpenSCAD executable', 'PASS' if openscad_ready else 'ENV_BLOCKED', 'required for SCAD regeneration unless CadQuery/other kernel is used'),
        CheckResult('Artifact/cache write access', 'PASS' if check_writable_directory(root / 'milestones') else 'ENV_BLOCKED', 'milestones directory must be writable'),
    ]

    kernel_ready = cadquery_ready or openscad_ready
    checks.append(CheckResult('Sample STL round-trip load', 'PASS' if stl_round_trip else 'ENV_BLOCKED', 'writes and loads a tiny STL through trimesh'))
    checks.append(CheckResult('CAD kernel/export path', 'PASS' if kernel_ready else 'ENV_BLOCKED', 'CadQuery or OpenSCAD must be available before final CAD generation'))
    return checks


def iter_milestone_dirs(root: Path) -> list[Path]:
    milestones_dir = root / 'milestones'
    if not milestones_dir.exists():
        return []
    return sorted(
        (child for child in milestones_dir.iterdir() if child.is_dir() and (child / 'milestone.yaml').exists()),
        key=lambda path: path.name,
    )


def check_cobra_skills(skills_root: Path) -> CheckResult:
    missing = [
        skill_name
        for skill_name in COMPANION_SKILLS
        if not (skills_root / skill_name / 'SKILL.md').exists()
    ]
    if missing:
        return CheckResult(
            'CoBrA skill sync',
            'WARN',
            f'missing {", ".join(missing)} under {skills_root}; local Zen CAD use still works',
        )
    return CheckResult('CoBrA skill sync', 'PASS', f'installed under {skills_root}')


def command_doctor(args: argparse.Namespace) -> int:
    root = find_repo_root(Path.cwd(), args.root)
    skills_root = Path(args.cobra_skills_root).expanduser() if args.cobra_skills_root else default_cobra_skills_root()

    print('Zen CAD doctor')
    print(f'Repository root: {root}')
    print(f'Current directory: {Path.cwd().resolve()}')
    print(f'Python: {sys.version.split()[0]}')

    repo_checks = [
        CheckResult('Repository root', 'PASS', 'Zen CAD files detected'),
        run_required_file_check(root),
        run_schema_check(root),
        check_cobra_skills(skills_root),
    ]
    env_checks = cad_toolchain_checks(root)

    print_section('Repository checks')
    for check in repo_checks:
        print_check(check)

    print_section('CAD toolchain preflight')
    for check in env_checks:
        print_check(check)

    blocked = [check for check in repo_checks if check.status == 'BLOCKED']
    env_blocked = [check for check in env_checks if check.status == 'ENV_BLOCKED']
    print_section('CoBrA workspace note')
    print('CoBrA skill sync installs the workflow skills only.')
    print('It does not register this repository as the active CoBrA workspace.')
    print(f'Start CoBrA from this repo, or explicitly point the agent to: {root}')

    if blocked:
        print_section('Zen CAD doctor: BLOCKED')
        print('Smallest unblock step:')
        print(f'- Run: {sys.executable} scripts/setup_zen_cad.py')
        return 1
    if env_blocked:
        print_section('CAD generation preflight: ENV_BLOCKED')
        print('Missing CAD/mesh capabilities:')
        for check in env_blocked:
            print(f'- {check.name}: {check.detail}')
        print('Smallest unblock step:')
        print('- Install or expose the missing CAD toolchain before running source-to-CAD/export gates.')
        if args.cad_required:
            return 2

    print_section('Zen CAD doctor: PASS')
    print('Next:')
    print('- In CoBrA/Codex/Claude Code/Cursor, ask: 기어 박스를 만들고 싶어')
    print('- Manual terminal fallback: ./zen-cad new "기어 박스를 만들고 싶어"')
    print('- Validate structure: ./zen-cad validate --level structure milestones/<id>')
    print('- Validate completion evidence: ./zen-cad validate --level completion milestones/<id>')
    return 0


def command_init(args: argparse.Namespace) -> int:
    root = find_repo_root(Path.cwd(), args.root)
    setup_args: list[str] = ['--root', str(root)]
    if args.with_cobra:
        skills_root = Path(args.cobra_skills_root).expanduser() if args.cobra_skills_root else default_cobra_skills_root()
        setup_args.extend(['--sync-cobra-skill', '--cobra-skill-dir', str(skills_root / 'agentic-cad')])
    if args.milestone_request:
        setup_args.extend(['--milestone-request', args.milestone_request])
    if args.milestone_id or args.milestone_title:
        if not (args.milestone_id and args.milestone_title):
            raise SystemExit('ERROR: use --milestone-id and --milestone-title together')
        setup_args.extend(['--milestone-id', args.milestone_id, '--milestone-title', args.milestone_title])
    if args.skip_validation:
        setup_args.append('--skip-validation')

    print('Zen CAD init')
    completed = run_python(root, 'scripts/setup_zen_cad.py', setup_args)
    print_command_output(completed)
    if completed.returncode != 0:
        print('\nZen CAD init: BLOCKED')
        print('Smallest unblock step:')
        print('- Review the setup output above and rerun ./zen-cad doctor')
        return completed.returncode

    print('\nZen CAD init: PASS')
    if args.with_cobra:
        print('CoBrA skill sync: PASS')
        print('Important: this installed skills only; it did not bind CoBrA to this repo.')
        print(f'Start CoBrA from: {root}')
    print('Next:')
    print('- Check the environment: ./zen-cad doctor')
    print('- Create a milestone: ./zen-cad new "기어 박스를 만들고 싶어"')
    return 0


def command_new(args: argparse.Namespace) -> int:
    root = find_repo_root(Path.cwd(), args.root)
    request = ' '.join(args.request_words).strip()
    wizard_notes = ''

    if args.wizard:
        request, wizard_notes = run_new_wizard(request)
    if not request and not (args.milestone_id and args.milestone_title):
        raise SystemExit('ERROR: provide a request, or use --wizard, or use --id and --title')

    new_args: list[str] = ['--root', str(root)]
    if args.milestone_id:
        new_args.extend(['--id', args.milestone_id])
    if args.milestone_title:
        new_args.extend(['--title', args.milestone_title])
    if request:
        new_args.extend(['--request', request])

    print('Zen CAD new milestone')
    completed = run_python(root, 'scripts/new_milestone.py', new_args)
    print_command_output(completed)
    if completed.returncode != 0:
        print('\nMilestone creation: BLOCKED')
        print('Smallest unblock step:')
        print('- Pick a unique milestone id or rerun with a different request.')
        return completed.returncode

    milestone_path = parse_created_milestone(completed.stdout)
    if milestone_path is not None and wizard_notes:
        append_wizard_notes(milestone_path, wizard_notes)

    print('\nMilestone creation: PASS')
    if milestone_path is not None:
        rel = milestone_path.relative_to(root) if milestone_path.is_relative_to(root) else milestone_path
        print(f'Active milestone: {rel}')
        print('Next:')
        print(f'- Open: {rel}/00_requirements/requirements_brief.md')
        print(f'- Continue with /agentic-cad using {rel} as the active CAD job.')
        print(f'- Validate structure and evidence: ./zen-cad validate {rel}')
    return 0


def run_new_wizard(initial_request: str) -> tuple[str, str]:
    print('Zen CAD new milestone wizard')
    goal = initial_request or input('What do you want to design? ').strip()
    if not goal:
        raise SystemExit('ERROR: wizard needs a design goal')
    scope = prompt_with_default('Scope (part/assembly)', 'assembly')
    units = prompt_with_default('Units (mm/inch)', 'mm')
    source_first = prompt_with_default('Need standard part sourcing? (yes/no)', 'yes')
    exports = prompt_with_default('Expected exports', 'STEP, STL')
    target = prompt_with_default('Target maturity (concept/demo/production-ready)', 'concept')
    validation = prompt_with_default('Validation focus', 'dimensions, interference, connections, BOM')
    notes = (
        '\n## Wizard intake\n\n'
        f'- Scope: {scope}\n'
        f'- Units: {units}\n'
        f'- Standard part sourcing needed: {source_first}\n'
        f'- Expected exports: {exports}\n'
        f'- Target maturity: {target}\n'
        f'- Validation focus: {validation}\n'
    )
    return goal, notes


def prompt_with_default(label: str, default: str) -> str:
    value = input(f'{label} [{default}]: ').strip()
    return value or default


def parse_created_milestone(output: str) -> Path | None:
    for line in output.splitlines():
        if line.startswith('Created milestone: '):
            return Path(line.removeprefix('Created milestone: ')).expanduser().resolve()
    return None


def append_wizard_notes(milestone: Path, notes: str) -> None:
    requirements = milestone / '00_requirements/requirements_brief.md'
    if requirements.exists():
        with requirements.open('a', encoding='utf-8') as file:
            file.write(notes)


def command_validate(args: argparse.Namespace) -> int:
    root = find_repo_root(Path.cwd(), args.root)
    targets = resolve_validation_targets(root, args.milestones)
    level = getattr(args, 'level', 'all')
    completion_required = getattr(args, 'completion_required', False)

    print('Zen CAD validation')
    root_checks = [
        run_required_file_check(root),
        run_schema_check(root),
    ]
    print_section('Repository checks')
    for check in root_checks:
        print_check(check)
    if any(check.status == 'BLOCKED' for check in root_checks):
        print_section('Zen CAD validation result: BLOCKED')
        print('Smallest unblock step:')
        print('- Fix the repository-level file/schema errors above.')
        return 1

    blocked_milestones: list[Path] = []
    evidence_blocked: list[tuple[Path, list[GateResult]]] = []
    for milestone in targets:
        result = validate_single_milestone(root, milestone)
        if result.returncode != 0:
            blocked_milestones.append(milestone)
            print_section(f'Milestone: {milestone.name}')
            print('[BLOCKED] Milestone structure')
            print(first_line(result.stdout or result.stderr))
            continue
        print_milestone_summary(root, milestone)
        if level in {'all', 'completion'} or completion_required:
            gates = analyze_completion_gates(root, milestone)
            print_completion_gate_summary(gates)
            if blocking_gates(gates):
                evidence_blocked.append((milestone, gates))

    if blocked_milestones:
        print_section('Zen CAD validation result: BLOCKED')
        print('Reason:')
        for milestone in blocked_milestones:
            print(f'- {milestone.relative_to(root)} did not pass structure validation')
        return 1

    if level == 'completion':
        if evidence_blocked:
            print_section('Zen CAD completion validation result: BLOCKED')
            print('Reason:')
            for milestone, gates in evidence_blocked:
                _, reason = completion_evidence_status_from_gates(gates)
                print(f'- {milestone.relative_to(root)}: {reason}')
            return 2
        print_section('Zen CAD completion validation result: PASS')
        print('Scope: source-lock, CAD exports, assembly contract, CAD-kernel evidence, BOM, and final report.')
        return 0

    print_section('Zen CAD validation result: PASS')
    print('Scope: required files, JSON schemas, BOM headers, and milestone structure.')
    if level == 'structure':
        return 0
    if evidence_blocked:
        print('\nCompletion evidence: BLOCKED')
        print('Blocking gates:')
        for milestone, gates in evidence_blocked:
            for gate in blocking_gates(gates):
                print(f'- {milestone.relative_to(root)} {gate.gate_id} {gate.name}: {gate.detail}')
        print('Smallest unblock step:')
        all_steps = dedupe_preserving_order(
            [step for _, gates in evidence_blocked for gate in blocking_gates(gates) for step in gate.smallest_unblock_steps]
        )
        print(f'- {all_steps[0] if all_steps else "Resolve the blocking completion gates above."}')
        if completion_required:
            return 2
    else:
        print('Completion evidence: PASS')
    return 0


def command_validate_structure(args: argparse.Namespace) -> int:
    args.level = 'structure'
    args.completion_required = False
    return command_validate(args)


def command_validate_completion(args: argparse.Namespace) -> int:
    args.level = 'completion'
    args.completion_required = True
    return command_validate(args)


def command_source_lock(args: argparse.Namespace) -> int:
    root = find_repo_root(Path.cwd(), args.root)
    targets = resolve_validation_targets(root, args.milestones)

    print('Zen CAD source-lock audit')
    blocked = False
    for milestone in targets:
        print_section(f'Milestone: {milestone.name}')
        audits = audit_source_locks(milestone)
        for audit in audits:
            marker = 'PASS' if not audit.blockers else 'BLOCKED'
            eligible = 'true' if audit.completion_eligible else 'false'
            print(f'[{marker}] {audit.part_id} {audit.name}')
            print(f'  classification: {audit.classification}')
            print(f'  status: {audit.status}')
            print(f'  completion_eligible: {eligible}')
            for blocker in audit.blockers:
                print(f'  - {blocker}')
            blocked = blocked or bool(audit.blockers)

    if blocked:
        print_section('Source-lock: BLOCKED')
        print('Smallest unblock step:')
        print('- For every standard part, record status source_locked with supplier, SKU, source URL, datasheet, cached STEP/STP, and verified critical dimensions.')
        return 0 if args.audit_only else 2

    print_section('Source-lock: PASS')
    return 0


def render_blocked_report(root: Path, milestone: Path, gates: list[GateResult]) -> str:
    blocked = blocking_gates(gates)
    passed = [gate for gate in gates if gate.status == 'PASS']
    verdict = 'BLOCKED' if blocked else 'PASS'
    steps = dedupe_preserving_order([step for gate in blocked for step in gate.smallest_unblock_steps])
    rel = milestone.relative_to(root) if milestone.is_relative_to(root) else milestone

    lines = [
        f'# Blocked Report: {milestone.name}',
        '',
        f'Verdict: {verdict}',
        '',
        f'Milestone: {rel}',
        '',
        '## Completed',
    ]
    if passed:
        lines.extend(f'- {gate.gate_id} {gate.name}: {gate.detail}' for gate in passed)
    else:
        lines.append('- No completion gates passed yet.')

    lines.extend(['', '## Blocked'])
    if blocked:
        lines.extend(f'- {gate.gate_id} {gate.name}: {gate.detail}' for gate in blocked)
    else:
        lines.append('- No blocking completion gates.')

    lines.extend(['', '## Smallest Unblock Step'])
    lines.append(f'- {steps[0]}' if steps else '- No unblock step required.')

    lines.extend(
        [
            '',
            '## Evidence Policy',
            '',
            '- Structure PASS is not completion PASS.',
            '- Proxy STL/GLB/viewer artifacts are preview/debug only.',
            '- Standard parts require source_locked manifest records and cached STEP/STP files.',
            '- CAD completion requires reproducible kernel/export/contact/clearance evidence.',
            '',
        ]
    )
    return '\n'.join(lines)


def command_blocked_report(args: argparse.Namespace) -> int:
    root = find_repo_root(Path.cwd(), args.root)
    targets = resolve_validation_targets(root, args.milestones)

    print('Zen CAD blocked report')
    for milestone in targets:
        gates = analyze_completion_gates(root, milestone)
        report = render_blocked_report(root, milestone, gates)
        print_section(f'Milestone: {milestone.name}')
        print(report)
        if args.write:
            target = milestone / '07_report/blocked_report.md'
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(report, encoding='utf-8')
            display = target.relative_to(root) if target.is_relative_to(root) else target
            print(f'Wrote: {display}')
    return 0


def resolve_validation_targets(root: Path, milestone_args: list[str]) -> list[Path]:
    if not milestone_args:
        return [milestone for milestone in iter_milestone_dirs(root) if milestone.name != '_template']
    targets = []
    for value in milestone_args:
        path = Path(value).expanduser()
        if not path.is_absolute():
            path = root / path
        targets.append(path.resolve())
    return targets


def validate_single_milestone(root: Path, milestone: Path) -> subprocess.CompletedProcess[str]:
    return run_python(root, 'scripts/validate_milestone.py', [str(milestone)])


def print_milestone_summary(root: Path, milestone: Path) -> None:
    print_section(f'Milestone: {milestone.name}')
    print('[PASS] Milestone structure')
    print('Generated / expected evidence files:')
    for label, rel in MILESTONE_ARTIFACTS:
        path = milestone / rel
        status = 'present' if path.exists() else 'missing'
        display = path.relative_to(root) if path.is_relative_to(root) else path
        print(f'- {label}: {display} ({status})')


def load_selected_parts(milestone: Path) -> tuple[list[dict[str, object]], str]:
    manifest_path = milestone / '02_parts/selected_parts_manifest.json'
    data, error = read_json_file(manifest_path)
    if data is None:
        return [], f'selected_parts_manifest.json is not readable JSON: {error}'
    parts = data.get('parts')
    if not isinstance(parts, list):
        return [], 'selected_parts_manifest.json has no parts array'
    dict_parts = [part for part in parts if isinstance(part, dict)]
    if len(dict_parts) != len(parts):
        return dict_parts, 'selected_parts_manifest.json contains non-object part rows'
    return dict_parts, ''


def audit_source_locks(milestone: Path) -> list[PartAudit]:
    parts, error = load_selected_parts(milestone)
    if error:
        return [
            PartAudit(
                part_id='manifest',
                name='selected_parts_manifest.json',
                classification='unknown',
                status='blocked',
                completion_eligible=False,
                blockers=[error],
                smallest_unblock_steps=['Repair 02_parts/selected_parts_manifest.json before sourcing or CAD work continues.'],
            )
        ]

    audits: list[PartAudit] = []
    for part in parts:
        part_id = str(part.get('part_id') or 'unknown_part')
        name = str(part.get('name') or part_id)
        classification = str(part.get('classification') or 'unknown')
        explicit_status = str(part.get('status') or '').strip()
        proxy_part = bool(part.get('proxy_part')) or classification == 'placeholder_proxy'
        completion_eligible = bool(part.get('completion_eligible', not proxy_part))
        blockers: list[str] = []
        steps: list[str] = []

        if proxy_part:
            completion_eligible = False
            blockers.append('proxy_only artifacts are completion-ineligible')
            steps.append(f'Replace {part_id} with a source_locked catalog part or an explicitly custom design-specific part.')

        if classification in {'off_the_shelf', 'semi_standard_configurable'}:
            source_url = value_from_any(part, 'source_url')
            datasheet_url = value_from_any(part, 'datasheet_url')
            supplier = value_from_any(part, 'supplier', 'manufacturer')
            sku = value_from_any(part, 'sku', 'part_number')
            step_file = value_from_any(part, 'step_file', 'step_path')
            dimensions_verified = part.get('critical_dimensions_verified')
            if dimensions_verified is None:
                dimensions_verified = part.get('geometry_match')

            if explicit_status != 'source_locked':
                blockers.append(f'status is {explicit_status!r}, not "source_locked"')
            if not is_meaningful(supplier):
                blockers.append('supplier/manufacturer is missing')
            if not is_meaningful(sku):
                blockers.append('sku/part_number is missing')
            if not is_meaningful(source_url):
                blockers.append('source_url is missing')
            if not is_meaningful(datasheet_url):
                blockers.append('datasheet_url is missing')
            if not local_artifact_exists(milestone, step_file):
                blockers.append('STEP/STP file is missing or empty')
            if dimensions_verified is not True:
                blockers.append('critical_dimensions_verified is not true')

            if blockers:
                steps.append(
                    f'Source-lock {part_id} with supplier, SKU, source URL, datasheet, cached STEP/STP, and verified critical dimensions.'
                )

        if completion_eligible is False and not proxy_part:
            blockers.append('completion_eligible is false')
            steps.append(f'Mark {part_id} completion_eligible true only after its final evidence is attached.')

        status = 'source_locked' if not blockers else ('proxy_only' if proxy_part else 'blocked')
        audits.append(
            PartAudit(
                part_id=part_id,
                name=name,
                classification=classification,
                status=status,
                completion_eligible=completion_eligible,
                blockers=blockers,
                smallest_unblock_steps=dedupe_preserving_order(steps),
            )
        )
    return audits


def dedupe_preserving_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def nonempty_artifacts(path: Path, suffixes: set[str]) -> list[Path]:
    if not path.exists():
        return []
    return sorted(
        candidate
        for candidate in path.rglob('*')
        if candidate.is_file() and candidate.suffix.casefold() in suffixes and candidate.stat().st_size > 0
    )


def validation_report_status(milestone: Path) -> tuple[str, list[str], str]:
    validation_report = milestone / '05_validation/validation_report.json'
    data, error = read_json_file(validation_report)
    if data is None:
        return 'blocked', [f'validation_report.json is not readable JSON: {error}'], ''
    status = data.get('status')
    checks = data.get('checks')
    blockers: list[str] = []
    if status != 'pass':
        blockers.append(f'validation_report status is {status!r}, not "pass"')
    if isinstance(checks, list):
        not_passed = [
            str(check.get('check_id') or check.get('name') or index)
            for index, check in enumerate(checks)
            if isinstance(check, dict) and check.get('result') != 'pass'
        ]
        if not_passed:
            blockers.append(f'validation checks not passing: {", ".join(not_passed)}')
    else:
        blockers.append('validation_report checks array is missing')
    summary = str(data.get('summary') or '')
    return str(status), blockers, summary


def analyze_completion_gates(root: Path, milestone: Path) -> list[GateResult]:
    gates: list[GateResult] = []
    validation_status, validation_blockers, validation_summary = validation_report_status(milestone)

    env_checks = cad_toolchain_checks(root)
    env_blockers = [check for check in env_checks if check.status == 'ENV_BLOCKED']
    gate0_pass = validation_status == 'pass' and not validation_blockers
    if gate0_pass or not env_blockers:
        gates.append(GateResult('Gate 0', 'doctor / environment preflight', 'PASS', 'CAD environment evidence is available.', []))
    else:
        missing = ', '.join(check.name for check in env_blockers)
        gates.append(
            GateResult(
                'Gate 0',
                'doctor / environment preflight',
                'BLOCKED',
                f'ENV_BLOCKED: {missing}',
                ['Run ./zen-cad doctor --cad-required and install or expose the missing CAD/mesh toolchain.'],
            )
        )

    requirements = milestone / '00_requirements/requirements_brief.md'
    req_text = requirements.read_text(encoding='utf-8') if requirements.exists() else ''
    if requirements.exists() and len(req_text.strip()) > 40 and 'REPLACE_WITH' not in req_text and 'TBD' not in req_text:
        gates.append(GateResult('Gate 1', 'requirement normalization', 'PASS', 'requirements brief exists and is non-template.', []))
    else:
        gates.append(
            GateResult(
                'Gate 1',
                'requirement normalization',
                'BLOCKED',
                'requirements brief is missing, empty, or still templated',
                ['Normalize measurable requirements, assumptions, units, target exports, and completion criteria.'],
            )
        )

    audits = audit_source_locks(milestone)
    source_blockers = [audit for audit in audits if audit.blockers]
    if source_blockers:
        detail = '; '.join(f'{audit.part_id}: {", ".join(audit.blockers[:3])}' for audit in source_blockers[:5])
        steps = [step for audit in source_blockers for step in audit.smallest_unblock_steps]
        gates.append(GateResult('Gate 2', 'standard part source-lock', 'BLOCKED', detail, dedupe_preserving_order(steps)))
    else:
        gates.append(GateResult('Gate 2', 'standard part source-lock', 'PASS', 'all standard parts are source_locked and completion-eligible.', []))

    cad_sources = nonempty_artifacts(milestone / '03_cad', {'.py', '.scad', '.cq', '.fcstd'})
    cad_exports = nonempty_artifacts(milestone / '03_cad', {'.step', '.stp', '.stl', '.brep'})
    proxy_validation = milestone / '05_validation/custom_cad_proxy_validation.json'
    proxy_only = False
    if proxy_validation.exists():
        proxy_data, _ = read_json_file(proxy_validation)
        proxy_status = str((proxy_data or {}).get('status') or '').casefold()
        proxy_only = 'proxy' in proxy_status
    if cad_sources and cad_exports and not proxy_only:
        gates.append(GateResult('Gate 3', 'custom CAD generation', 'PASS', 'custom CAD source and exports are present.', []))
    else:
        details = []
        if not cad_sources:
            details.append('custom CAD source missing')
        if not cad_exports:
            details.append('custom CAD exports missing')
        if proxy_only:
            details.append('custom CAD evidence is proxy-only')
        gates.append(
            GateResult(
                'Gate 3',
                'custom CAD generation',
                'BLOCKED',
                ', '.join(details) or 'custom CAD final evidence missing',
                ['Generate design-specific CAD only, export final STEP/STL as required, and keep proxy exports out of completion evidence.'],
            )
        )

    contact_map, contact_error = read_json_file(milestone / '04_assembly/contact_map.json')
    connections, connection_error = read_json_file(milestone / '04_assembly/connections.json')
    contacts = contact_map.get('contacts') if contact_map else None
    connection_rows = connections.get('connections') if connections else None
    if isinstance(contacts, list) and contacts and isinstance(connection_rows, list) and connection_rows:
        gates.append(GateResult('Gate 4', 'assembly contract', 'PASS', 'CONTACT_MAP and CONNECTIONS contain assembly rows.', []))
    else:
        blockers = []
        if contact_error:
            blockers.append(f'CONTACT_MAP invalid: {contact_error}')
        elif not contacts:
            blockers.append('CONTACT_MAP has no contacts')
        if connection_error:
            blockers.append(f'CONNECTIONS invalid: {connection_error}')
        elif not connection_rows:
            blockers.append('CONNECTIONS has no connections')
        gates.append(
            GateResult(
                'Gate 4',
                'assembly contract',
                'BLOCKED',
                '; '.join(blockers),
                ['Define contact and connection rows that reference sourced and custom parts before assembly validation.'],
            )
        )

    normalized_metadata = milestone / '02_parts/normalized_step_metadata.json'
    metadata_blocked = False
    if normalized_metadata.exists():
        metadata_data, metadata_error = read_json_file(normalized_metadata)
        metadata_status = str((metadata_data or {}).get('status') or '').casefold()
        metadata_blocked = bool(metadata_error) or 'blocked' in metadata_status or 'no_step' in metadata_status
    standard_step_missing = [
        audit.part_id
        for audit in audits
        if audit.classification in {'off_the_shelf', 'semi_standard_configurable'}
        and any('STEP/STP file' in blocker for blocker in audit.blockers)
    ]
    final_step_exports = nonempty_artifacts(milestone / '03_cad', {'.step', '.stp'})
    if not metadata_blocked and not standard_step_missing and final_step_exports:
        gates.append(GateResult('Gate 5', 'export/cache verification', 'PASS', 'STEP cache/metadata and final exports are present.', []))
    else:
        blockers = []
        if metadata_blocked or not normalized_metadata.exists():
            blockers.append('normalized STEP metadata is missing or blocked')
        if standard_step_missing:
            blockers.append(f'standard STEP/STP missing for {", ".join(standard_step_missing[:5])}')
        if not final_step_exports:
            blockers.append('final STEP/STP exports are missing')
        gates.append(
            GateResult(
                'Gate 5',
                'export/cache verification',
                'BLOCKED',
                '; '.join(blockers),
                ['Cache source-backed STEP/STP files, normalize metadata, and export final STEP/STP artifacts before completion.'],
            )
        )

    if validation_blockers:
        gates.append(
            GateResult(
                'Gate 6',
                'CAD-kernel validation',
                'BLOCKED',
                '; '.join(validation_blockers),
                ['Run kernel-backed load/export/solid/contact/clearance checks and update validation_report.json only with reproducible pass evidence.'],
            )
        )
    else:
        gates.append(GateResult('Gate 6', 'CAD-kernel validation', 'PASS', 'validation_report status and checks are pass.', []))

    bom_path = milestone / '06_bom/bom.csv'
    final_report = milestone / '07_report/final_engineering_report.md'
    report_text = final_report.read_text(encoding='utf-8') if final_report.exists() else ''
    bom_has_rows = False
    if bom_path.exists():
        try:
            with bom_path.open(newline='', encoding='utf-8') as file:
                bom_has_rows = sum(1 for _ in file) > 1
        except Exception:
            bom_has_rows = False
    report_blocked_language = any(token in (validation_summary + '\n' + report_text).casefold() for token in ['blocked', 'not completion-ready'])
    if bom_has_rows and final_report.exists() and validation_status == 'pass' and not report_blocked_language:
        gates.append(GateResult('Gate 7', 'final report / BOM / evidence bundle', 'PASS', 'BOM and final report align with pass evidence.', []))
    else:
        blockers = []
        if not bom_has_rows:
            blockers.append('BOM has no rows')
        if not final_report.exists():
            blockers.append('final report missing')
        if report_blocked_language:
            blockers.append('report or validation summary still declares blocked/not completion-ready')
        if validation_status != 'pass':
            blockers.append('validation_report is not pass')
        gates.append(
            GateResult(
                'Gate 7',
                'final report / BOM / evidence bundle',
                'BLOCKED',
                '; '.join(blockers),
                ['Publish a truthful PASS or BLOCKED final report with BOM, blockers, and smallest unblock step.'],
            )
        )

    return gates


def blocking_gates(gates: list[GateResult]) -> list[GateResult]:
    return [gate for gate in gates if gate.status == 'BLOCKED']


def completion_evidence_status_from_gates(gates: list[GateResult]) -> tuple[str, str]:
    blocked = blocking_gates(gates)
    if not blocked:
        return 'PASS', ''
    detail = '; '.join(f'{gate.gate_id} {gate.name}: {gate.detail}' for gate in blocked)
    return 'BLOCKED', detail


def print_completion_gate_summary(gates: list[GateResult]) -> None:
    blocked = blocking_gates(gates)
    if not blocked:
        print('Completion evidence: PASS')
        return
    print('Completion evidence: BLOCKED')
    print('Blocking gates:')
    for gate in blocked:
        print(f'- {gate.gate_id} {gate.name}: {gate.detail}')
    steps = dedupe_preserving_order([step for gate in blocked for step in gate.smallest_unblock_steps])
    if steps:
        print('Smallest unblock step:')
        print(f'- {steps[0]}')


def completion_evidence_status(milestone: Path) -> tuple[str, str]:
    validation_report = milestone / '05_validation/validation_report.json'
    try:
        data = json.loads(validation_report.read_text(encoding='utf-8'))
    except Exception as exc:
        return 'BLOCKED', f'validation_report.json is not readable JSON: {exc}'
    status = data.get('status')
    checks = data.get('checks')
    if status != 'pass':
        return 'BLOCKED', f'validation_report status is {status!r}, not "pass"'
    if isinstance(checks, list):
        not_passed = [
            str(check.get('check_id') or check.get('name') or index)
            for index, check in enumerate(checks)
            if isinstance(check, dict) and check.get('result') != 'pass'
        ]
        if not_passed:
            return 'BLOCKED', f'validation checks not passing: {", ".join(not_passed)}'
    return 'PASS', ''


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='First-run friendly CLI for Zen CAD.')
    parser.add_argument('--root', help='Zen CAD repository root. Defaults to current directory or nearest parent.')
    subparsers = parser.add_subparsers(dest='command', required=True)

    doctor = subparsers.add_parser('doctor', help='Check repo health, schema validation, CoBrA skill sync, and CAD toolchain state.')
    add_root_argument(doctor)
    doctor.add_argument('--cobra-skills-root', help='CoBrA skills root. Defaults to COBRA_SKILLS_ROOT, COBRA_WORKSPACE/skills, or ~/.cobra/workspace/skills.')
    doctor.add_argument('--cad-required', action='store_true', help='Return ENV_BLOCKED when CAD/mesh/kernel tooling is missing.')
    doctor.set_defaults(func=command_doctor)

    init = subparsers.add_parser('init', help='Run setup and optionally sync CoBrA skills.')
    add_root_argument(init)
    init.add_argument('--with-cobra', action='store_true', help='Sync bundled Zen CAD skills into CoBrA.')
    init.add_argument('--cobra-skills-root', help='CoBrA skills root. The agentic-cad skill is installed as a child of this directory.')
    init.add_argument('--milestone-request', help='Create a milestone from a natural-language request during init.')
    init.add_argument('--milestone-id', help='Explicit milestone id, e.g. 002_gearbox.')
    init.add_argument('--milestone-title', help='Human-readable title for --milestone-id.')
    init.add_argument('--skip-validation', action='store_true', help='Skip built-in validation during init.')
    init.set_defaults(func=command_init)

    new = subparsers.add_parser('new', help='Create a milestone from a natural-language CAD request.')
    add_root_argument(new)
    new.add_argument('request_words', nargs='*', help='Natural-language CAD request.')
    new.add_argument('--wizard', action='store_true', help='Ask guided first-milestone intake questions.')
    new.add_argument('--id', dest='milestone_id', help='Explicit milestone id, e.g. 002_gearbox.')
    new.add_argument('--title', dest='milestone_title', help='Human-readable title for --id.')
    new.set_defaults(func=command_new)

    validate = subparsers.add_parser('validate', help='Validate repo/milestone structure and optional completion evidence gates.')
    add_root_argument(validate)
    validate.add_argument('milestones', nargs='*', help='Milestone paths to validate. Defaults to all milestones.')
    validate.add_argument('--level', choices=['all', 'structure', 'completion'], default='all', help='Validation level. all keeps structure exit-code compatibility while printing completion gates.')
    validate.add_argument('--completion-required', action='store_true', help='Return non-zero when validation_report.json does not show completion evidence pass.')
    validate.set_defaults(func=command_validate)

    validate_structure = subparsers.add_parser('validate-structure', help='Validate only required files, schemas, BOM headers, and milestone structure.')
    add_root_argument(validate_structure)
    validate_structure.add_argument('milestones', nargs='*', help='Milestone paths to validate. Defaults to all milestones.')
    validate_structure.set_defaults(func=command_validate_structure)

    validate_completion = subparsers.add_parser('validate-completion', help='Validate completion evidence gates and return non-zero when blocked.')
    add_root_argument(validate_completion)
    validate_completion.add_argument('milestones', nargs='*', help='Milestone paths to validate. Defaults to all milestones.')
    validate_completion.set_defaults(func=command_validate_completion)

    source_lock = subparsers.add_parser('source-lock', help='Audit standard-part source-lock status before CAD generation.')
    add_root_argument(source_lock)
    source_lock.add_argument('milestones', nargs='*', help='Milestone paths to audit. Defaults to all milestones.')
    source_lock.add_argument('--audit-only', action='store_true', help='Always return zero while printing source-lock blockers.')
    source_lock.set_defaults(func=command_source_lock)

    blocked_report = subparsers.add_parser('blocked-report', help='Render a truthful PASS/BLOCKED evidence report from completion gates.')
    add_root_argument(blocked_report)
    blocked_report.add_argument('milestones', nargs='*', help='Milestone paths to report. Defaults to all milestones.')
    blocked_report.add_argument('--write', action='store_true', help='Write 07_report/blocked_report.md in each milestone.')
    blocked_report.set_defaults(func=command_blocked_report)
    return parser


def add_root_argument(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        '--root',
        default=argparse.SUPPRESS,
        help='Zen CAD repository root. This can be placed after the subcommand.',
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == '__main__':
    raise SystemExit(main())
