#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
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

MATURITY_LEVELS = {'concept', 'layout', 'final'}

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


@dataclass
class ValidationReportAudit:
    status: str
    blockers: list[str]
    summary: str
    passed_check_ids: set[str]
    evidence_types: set[str]
    artifact_paths: set[Path]
    step_artifact_paths: set[Path]
    artifacts_by_role: dict[str, set[Path]]


COMPLETION_REQUIRED_EVIDENCE_TYPES = {
    'cad_generation',
    'step_load',
    'geometry_inspection',
}

ARTIFACT_REQUIRED_EVIDENCE_TYPES = {
    'cad_generation',
    'step_load',
    'geometry_inspection',
    'visual_snapshot',
}

STEP_ARTIFACT_ROLES = {'primary_step', 'step_export', 'step'}


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


def selected_python(explicit: str | None = None) -> str:
    return explicit or os.environ.get('ZEN_CAD_PYTHON') or sys.executable


def resolve_python(value: str) -> str:
    path = Path(value).expanduser()
    if path.exists():
        return str(path.absolute())
    found = shutil.which(value)
    return found or value


def current_python_probe() -> dict[str, object]:
    modules = {
        name: has_importable_module(name)
        for name in ['numpy', 'trimesh', 'build123d', 'cadquery', 'OCP']
    }
    return {
        'ok': True,
        'executable': sys.executable,
        'version': sys.version.split()[0],
        'in_virtualenv': sys.prefix != getattr(sys, 'base_prefix', sys.prefix),
        'modules': modules,
        'openscad': shutil.which('openscad'),
        'stl_round_trip': sample_stl_round_trip_passes(),
        'build123d_step_smoke': build123d_step_smoke_passes(),
    }


def external_python_probe(python_executable: str) -> dict[str, object]:
    probe = r'''
import importlib
import importlib.util
import json
import shutil
import sys
import tempfile
from pathlib import Path

def has_module(name):
    return importlib.util.find_spec(name) is not None

def stl_round_trip():
    if not has_module("trimesh"):
        return False
    try:
        trimesh = importlib.import_module("trimesh")
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
        with tempfile.NamedTemporaryFile("w", suffix=".stl", encoding="utf-8") as file:
            file.write(stl_text)
            file.flush()
            mesh = trimesh.load(file.name, force="mesh")
        return len(getattr(mesh, "vertices", [])) > 0 and len(getattr(mesh, "faces", [])) > 0
    except Exception:
        return False

def build123d_step_smoke():
    if not has_module("build123d") or not has_module("OCP"):
        return False
    try:
        build123d = importlib.import_module("build123d")
        step_control = importlib.import_module("OCP.STEPControl")
        if_select = importlib.import_module("OCP.IFSelect")
        with tempfile.NamedTemporaryFile(suffix=".step") as file:
            build123d.export_step(build123d.Box(10, 20, 2), file.name)
            if Path(file.name).stat().st_size <= 0:
                return False
            reader = step_control.STEPControl_Reader()
            return reader.ReadFile(file.name) == if_select.IFSelect_RetDone
    except Exception:
        return False

modules = {name: has_module(name) for name in ["numpy", "trimesh", "build123d", "cadquery", "OCP"]}
print(json.dumps({
    "ok": True,
    "executable": sys.executable,
    "version": sys.version.split()[0],
    "in_virtualenv": sys.prefix != getattr(sys, "base_prefix", sys.prefix),
    "modules": modules,
    "openscad": shutil.which("openscad"),
    "stl_round_trip": stl_round_trip(),
    "build123d_step_smoke": build123d_step_smoke(),
}))
'''
    completed = subprocess.run(
        [resolve_python(python_executable), '-c', probe],
        text=True,
        capture_output=True,
    )
    if completed.returncode != 0:
        return {
            'ok': False,
            'executable': python_executable,
            'error': first_line(completed.stderr or completed.stdout) or f'exit code {completed.returncode}',
        }
    try:
        data = json.loads(completed.stdout)
    except Exception as exc:
        return {'ok': False, 'executable': python_executable, 'error': f'invalid probe JSON: {exc}'}
    if isinstance(data, dict):
        return data
    return {'ok': False, 'executable': python_executable, 'error': 'probe JSON is not an object'}


def local_artifact_exists(milestone: Path, value: object) -> bool:
    if not is_meaningful(value) or not isinstance(value, str):
        return False
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = milestone / path
    return path.exists() and path.stat().st_size > 0


def resolve_artifact_path(milestone: Path, value: object) -> Path | None:
    if not is_meaningful(value) or not isinstance(value, str):
        return None
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = milestone / path
    return path.resolve()


def value_from_any(data: dict[str, object], *keys: str) -> object:
    for key in keys:
        value = data.get(key)
        if is_meaningful(value):
            return value
    return None


def milestone_maturity(milestone: Path, explicit: str | None = None) -> str:
    if explicit:
        return explicit
    milestone_file = milestone / 'milestone.yaml'
    if milestone_file.exists():
        for line in milestone_file.read_text(encoding='utf-8').splitlines():
            if line.strip().startswith('maturity:'):
                value = line.split(':', 1)[1].strip().strip('"\'')
                if value in MATURITY_LEVELS:
                    return value
    validation_report = milestone / '05_validation/validation_report.json'
    data, _ = read_json_file(validation_report)
    if data is not None:
        value = str(data.get('maturity') or '').strip()
        if value in MATURITY_LEVELS:
            return value
    return 'final'


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


def build123d_step_smoke_passes() -> bool:
    if not has_importable_module('build123d') or not has_importable_module('OCP'):
        return False
    try:
        build123d = importlib.import_module('build123d')
        step_control = importlib.import_module('OCP.STEPControl')
        if_select = importlib.import_module('OCP.IFSelect')
        with tempfile.NamedTemporaryFile(suffix='.step') as file:
            build123d.export_step(build123d.Box(10, 20, 2), file.name)
            if Path(file.name).stat().st_size <= 0:
                return False
            reader = step_control.STEPControl_Reader()
            return reader.ReadFile(file.name) == if_select.IFSelect_RetDone
    except Exception:
        return False


def cad_toolchain_checks(root: Path, python_executable: str | None = None) -> list[CheckResult]:
    requested_python = selected_python(python_executable)
    if Path(resolve_python(requested_python)) != Path(sys.executable):
        probe = external_python_probe(requested_python)
    else:
        probe = current_python_probe()
    if not probe.get('ok'):
        return [
            CheckResult('Python runtime', 'ENV_BLOCKED', f'{requested_python}: {probe.get("error", "probe failed")}'),
            CheckResult('Artifact/cache write access', 'PASS' if check_writable_directory(root / 'milestones') else 'ENV_BLOCKED', 'milestones directory must be writable'),
        ]

    modules = probe.get('modules') if isinstance(probe.get('modules'), dict) else {}
    version = str(probe.get('version') or 'unknown')
    cadquery_ready = bool(modules.get('cadquery'))
    openscad_ready = bool(probe.get('openscad'))
    build123d_ready = bool(modules.get('build123d'))
    ocp_ready = bool(modules.get('OCP'))
    build123d_step_smoke = bool(probe.get('build123d_step_smoke'))
    stl_round_trip = bool(probe.get('stl_round_trip'))
    kernel_ready = cadquery_ready or openscad_ready or build123d_step_smoke or (build123d_ready and ocp_ready)
    checks = [
        CheckResult('Python runtime', 'PASS' if tuple(int(part) for part in version.split('.')[:2] if part.isdigit()) >= (3, 10) else 'WARN', f'{probe.get("executable")} ({version}); Python 3.10+ recommended'),
        CheckResult('Python virtualenv', 'PASS' if bool(probe.get('in_virtualenv')) else 'WARN', 'active virtualenv' if bool(probe.get('in_virtualenv')) else 'not running inside a virtualenv'),
        CheckResult('numpy import', 'PASS' if modules.get('numpy') else 'ENV_BLOCKED', 'required for many CAD/mesh validation flows'),
        CheckResult('trimesh import', 'PASS' if modules.get('trimesh') else 'ENV_BLOCKED', 'required for STL/mesh loadability checks'),
        CheckResult('build123d import', 'PASS' if build123d_ready else 'WARN', 'preferred Zen CAD generation backend'),
        CheckResult('OCP import', 'PASS' if ocp_ready else 'WARN', 'preferred OpenCascade validation backend for build123d'),
        CheckResult('cadquery import', 'PASS' if cadquery_ready else 'WARN', 'optional alternate CAD kernel path'),
        CheckResult('OpenSCAD executable', 'PASS' if openscad_ready else 'WARN', 'optional alternate SCAD regeneration path'),
        CheckResult('Artifact/cache write access', 'PASS' if check_writable_directory(root / 'milestones') else 'ENV_BLOCKED', 'milestones directory must be writable'),
    ]
    checks.append(CheckResult('Sample STL round-trip load', 'PASS' if stl_round_trip else 'ENV_BLOCKED', 'writes and loads a tiny STL through trimesh'))
    checks.append(CheckResult('build123d STEP/OCP smoke', 'PASS' if build123d_step_smoke else 'WARN', 'creates a build123d box, exports STEP, and loads it through OCP'))
    checks.append(CheckResult('CAD kernel/export path', 'PASS' if kernel_ready else 'ENV_BLOCKED', 'build123d+OCP, CadQuery, or OpenSCAD must be available before final CAD generation'))
    return checks


def iter_milestone_dirs(root: Path) -> list[Path]:
    milestones_dir = root / 'milestones'
    if not milestones_dir.exists():
        return []
    return sorted(
        (child for child in milestones_dir.iterdir() if child.is_dir() and (child / 'milestone.yaml').exists()),
        key=lambda path: path.name,
    )


def check_cobra_skills(root: Path, skills_root: Path) -> CheckResult:
    missing = [
        skill_name
        for skill_name in COMPANION_SKILLS
        if not (skills_root / skill_name / 'SKILL.md').exists()
    ]
    if missing:
        return CheckResult(
            'CoBrA skill discovery',
            'WARN',
            f'missing {", ".join(missing)} under {skills_root}; run ./zen-cad init --with-cobra so CoBrA can discover Zen CAD skills',
        )
    stale = []
    unbound = []
    wrong_root = []
    for skill_name in COMPANION_SKILLS:
        source = root / 'skills' / skill_name / 'SKILL.md'
        target_dir = skills_root / skill_name
        target = target_dir / 'SKILL.md'
        if file_hash(source) != file_hash(target):
            stale.append(skill_name)
        bound_root = cobra_context_bound_root(target_dir)
        if bound_root is None:
            unbound.append(skill_name)
        elif bound_root != root:
            wrong_root.append(f'{skill_name} -> {bound_root}')
    if stale:
        return CheckResult('CoBrA skill freshness', 'WARN', f'stale {", ".join(stale)} under {skills_root}; rerun ./zen-cad init --with-cobra')
    if unbound:
        return CheckResult(
            'CoBrA workspace binding',
            'WARN',
            f'missing ZEN_CAD_WORKSPACE.md for {", ".join(unbound)} under {skills_root}; rerun ./zen-cad init --with-cobra',
        )
    if wrong_root:
        return CheckResult(
            'CoBrA workspace binding',
            'WARN',
            f'installed skills point at a different Zen CAD root: {"; ".join(wrong_root)}; rerun ./zen-cad init --with-cobra from {root}',
        )
    return CheckResult('CoBrA skill sync', 'PASS', f'installed, fresh, and bound to {root} under {skills_root}')


def cobra_context_bound_root(skill_dir: Path) -> Path | None:
    context = skill_dir / 'ZEN_CAD_WORKSPACE.md'
    if not context.exists():
        return None
    for line in context.read_text(encoding='utf-8').splitlines():
        if line.startswith('Repository root: '):
            value = line.removeprefix('Repository root: ').strip()
            if value:
                return Path(value).expanduser().resolve()
    return None


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command_doctor(args: argparse.Namespace) -> int:
    root = find_repo_root(Path.cwd(), args.root)
    skills_root = Path(args.cobra_skills_root).expanduser() if args.cobra_skills_root else default_cobra_skills_root()
    python_executable = selected_python(args.python)

    print('Zen CAD doctor')
    print(f'Repository root: {root}')
    print(f'Current directory: {Path.cwd().resolve()}')
    print(f'Python: {python_executable}')

    repo_checks = [
        CheckResult('Repository root', 'PASS', 'Zen CAD files detected'),
        run_required_file_check(root),
        run_schema_check(root),
        check_cobra_skills(root, skills_root),
    ]
    env_checks = cad_toolchain_checks(root, python_executable)

    print_section('Repository checks')
    for check in repo_checks:
        print_check(check)

    print_section('CAD toolchain preflight')
    for check in env_checks:
        print_check(check)

    blocked = [check for check in repo_checks if check.status == 'BLOCKED']
    env_blocked = [check for check in env_checks if check.status == 'ENV_BLOCKED']
    print_section('CoBrA workspace note')
    print('CoBrA skill sync installs the workflow skills and writes a ZEN_CAD_WORKSPACE.md binding.')
    print('It does not change CoBrA process cwd by itself.')
    print(f'Start CoBrA from this repo, or let the installed skill use its bound root: {root}')

    if blocked:
        print_section('Zen CAD doctor: BLOCKED')
        print('Smallest unblock step:')
        print(f'- Run: {sys.executable} scripts/setup_zen_cad.py')
        return 1
    if env_blocked:
        print_section('Strict CAD preflight: ENV_BLOCKED (final/release only)')
        print('Missing local CAD/mesh capabilities:')
        for check in env_blocked:
            print(f'- {check.name}: {check.detail}')
        print('Concept/layout guidance:')
        print('- Do not stop before CAD exists; use the harness available CAD path and record this as a final-gate blocker.')
        print('Smallest final-gate unblock step:')
        print('- Install or expose the missing CAD toolchain before strict final/release gates.')
        print('- If a working venv already exists, rerun with --python /path/to/venv/bin/python or set ZEN_CAD_PYTHON.')
        if args.cad_required:
            return 2

    print_section('Zen CAD doctor: PASS')
    print('Next:')
    print('- In CoBrA/Codex/Claude Code/Cursor, ask: NEMA17 mount plate를 만들어줘')
    print('- Generate the first concept/layout CAD artifact with the harness available CAD toolchain.')
    print('- Manual terminal fallback: ./zen-cad new "기어 박스를 만들고 싶어"')
    print('- First-pass check: ./zen-cad validate --level structure milestones/<id>')
    print('- Final/release gate: ./zen-cad validate --level completion milestones/<id>')
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
    if args.maturity:
        setup_args.extend(['--maturity', args.maturity])

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
        print('Installed skills include ZEN_CAD_WORKSPACE.md bindings for this repo.')
        print('Important: this does not change CoBrA process cwd by itself.')
        print(f'Start CoBrA from this repo when possible, or let the installed skill use its bound root: {root}')
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
    if args.maturity:
        new_args.extend(['--maturity', args.maturity])
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
    python_executable = selected_python(getattr(args, 'python', None))
    maturity_override = getattr(args, 'maturity', None)

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
            gates = analyze_completion_gates(root, milestone, python_executable, maturity_override)
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
    maturity_override = getattr(args, 'maturity', None)

    print('Zen CAD source-lock audit')
    blocked = False
    final_required = False
    for milestone in targets:
        maturity = milestone_maturity(milestone, maturity_override)
        print_section(f'Milestone: {milestone.name}')
        print(f'Maturity: {maturity}')
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
        final_required = final_required or maturity == 'final'

    if blocked:
        if not final_required:
            print_section('Source-lock: WARN')
            print('Source-lock blockers are allowed for concept/layout generation, but final completion remains ineligible.')
            return 0
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
    python_executable = selected_python(getattr(args, 'python', None))
    maturity_override = getattr(args, 'maturity', None)

    print('Zen CAD blocked report')
    for milestone in targets:
        gates = analyze_completion_gates(root, milestone, python_executable, maturity_override)
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

        if blockers:
            status = 'proxy_only' if proxy_part else 'blocked'
        elif explicit_status:
            status = explicit_status
        elif classification == 'custom_design_specific':
            status = 'generated_custom'
        else:
            status = 'source_locked'
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


def step_file_has_end_iso(path: Path) -> bool:
    try:
        tail = path.read_bytes()[-4096:]
    except Exception:
        return False
    return b'END-ISO-10303-21' in tail


def artifact_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def audit_validation_artifact(
    milestone: Path,
    check_id: str,
    artifact: object,
    index: int,
) -> tuple[list[str], Path | None, str]:
    prefix = f'check {check_id} artifact[{index}]'
    if not isinstance(artifact, dict):
        return [f'{prefix} is not an object'], None, ''

    path = resolve_artifact_path(milestone, artifact.get('path'))
    if path is None:
        return [f'{prefix} path is missing'], None, str(artifact.get('role') or '')

    blockers: list[str] = []
    role = str(artifact.get('role') or '')
    if not role:
        blockers.append(f'{prefix} role is missing')
    if not path.exists() or not path.is_file():
        blockers.append(f'{prefix} path does not exist: {artifact.get("path")}')
        return blockers, path, role
    size = path.stat().st_size
    if size <= 0:
        blockers.append(f'{prefix} is empty: {artifact.get("path")}')

    recorded_size = artifact.get('size_bytes')
    if not isinstance(recorded_size, int) or recorded_size != size:
        blockers.append(f'{prefix} size_bytes mismatch for {artifact.get("path")}')

    recorded_hash = str(artifact.get('sha256') or '').strip()
    if not recorded_hash:
        blockers.append(f'{prefix} sha256 is missing for {artifact.get("path")}')
    else:
        try:
            actual_hash = artifact_hash(path)
        except Exception as exc:
            blockers.append(f'{prefix} sha256 could not be calculated for {artifact.get("path")}: {exc}')
        else:
            if actual_hash != recorded_hash:
                blockers.append(f'{prefix} sha256 mismatch for {artifact.get("path")}')

    if path.suffix.casefold() in {'.step', '.stp'} and not step_file_has_end_iso(path):
        blockers.append(f'{prefix} STEP file is missing END-ISO-10303-21 terminator: {artifact.get("path")}')
    return blockers, path, role


def audit_pass_check_evidence(
    milestone: Path,
    check: dict[str, object],
    index: int,
) -> tuple[list[str], set[Path], set[Path], dict[str, set[Path]], str]:
    check_id = str(check.get('check_id') or index)
    blockers: list[str] = []
    evidence_type = str(check.get('evidence_type') or '').strip()
    if not evidence_type:
        blockers.append(f'check {check_id} evidence_type is missing')
    if not is_meaningful(check.get('evidence')):
        blockers.append(f'check {check_id} evidence is missing')

    command = check.get('command')
    if not isinstance(command, dict):
        blockers.append(f'check {check_id} command object is missing')
    else:
        argv = command.get('argv')
        if not isinstance(argv, list) or not argv or not all(isinstance(arg, str) and arg.strip() for arg in argv):
            blockers.append(f'check {check_id} command.argv must be a non-empty string array')
        if not is_meaningful(command.get('cwd')):
            blockers.append(f'check {check_id} command.cwd is missing')
        if command.get('exit_code') != 0:
            blockers.append(f'check {check_id} command.exit_code is not 0')

    artifacts = check.get('artifacts')
    if not isinstance(artifacts, list):
        blockers.append(f'check {check_id} artifacts array is missing')
        artifacts = []
    if evidence_type in ARTIFACT_REQUIRED_EVIDENCE_TYPES and not artifacts:
        blockers.append(f'check {check_id} {evidence_type} evidence has no artifacts')

    artifact_paths: set[Path] = set()
    step_artifact_paths: set[Path] = set()
    artifacts_by_role: dict[str, set[Path]] = {}
    for artifact_index, artifact in enumerate(artifacts):
        artifact_blockers, path, role = audit_validation_artifact(milestone, check_id, artifact, artifact_index)
        blockers.extend(artifact_blockers)
        if path is None:
            continue
        artifact_paths.add(path)
        if role:
            artifacts_by_role.setdefault(role, set()).add(path)
        if path.suffix.casefold() in {'.step', '.stp'} or role in STEP_ARTIFACT_ROLES:
            step_artifact_paths.add(path)

    return blockers, artifact_paths, step_artifact_paths, artifacts_by_role, evidence_type


def audit_validation_report(milestone: Path) -> ValidationReportAudit:
    validation_report = milestone / '05_validation/validation_report.json'
    data, error = read_json_file(validation_report)
    if data is None:
        return ValidationReportAudit(
            status='blocked',
            blockers=[f'validation_report.json is not readable JSON: {error}'],
            summary='',
            passed_check_ids=set(),
            evidence_types=set(),
            artifact_paths=set(),
            step_artifact_paths=set(),
            artifacts_by_role={},
        )

    status = str(data.get('status') or '')
    checks = data.get('checks')
    blockers: list[str] = []
    passed_check_ids: set[str] = set()
    evidence_types: set[str] = set()
    artifact_paths: set[Path] = set()
    step_artifact_paths: set[Path] = set()
    artifacts_by_role: dict[str, set[Path]] = {}

    if status != 'pass':
        blockers.append(f'validation_report status is {status!r}, not "pass"')
    if not isinstance(checks, list) or not checks:
        blockers.append('validation_report checks array is missing or empty')
        checks = []

    for index, check in enumerate(checks):
        if not isinstance(check, dict):
            blockers.append(f'validation check {index} is not an object')
            continue
        check_id = str(check.get('check_id') or index)
        result = check.get('result')
        if result != 'pass':
            blockers.append(f'validation check {check_id} result is {result!r}, not "pass"')
            continue
        passed_check_ids.add(check_id)
        check_blockers, check_artifacts, check_step_artifacts, check_artifacts_by_role, evidence_type = audit_pass_check_evidence(milestone, check, index)
        blockers.extend(check_blockers)
        if evidence_type:
            evidence_types.add(evidence_type)
        artifact_paths.update(check_artifacts)
        step_artifact_paths.update(check_step_artifacts)
        for role, paths in check_artifacts_by_role.items():
            artifacts_by_role.setdefault(role, set()).update(paths)

    if status == 'pass':
        missing_types = sorted(COMPLETION_REQUIRED_EVIDENCE_TYPES - evidence_types)
        if missing_types:
            blockers.append(f'validation_report is missing required completion evidence types: {", ".join(missing_types)}')
        if not step_artifact_paths:
            blockers.append('validation_report has no hashed STEP/STP artifact evidence')

    return ValidationReportAudit(
        status=status,
        blockers=blockers,
        summary=str(data.get('summary') or ''),
        passed_check_ids=passed_check_ids,
        evidence_types=evidence_types,
        artifact_paths=artifact_paths,
        step_artifact_paths=step_artifact_paths,
        artifacts_by_role=artifacts_by_role,
    )


def validation_report_status(milestone: Path) -> tuple[str, list[str], str]:
    audit = audit_validation_report(milestone)
    return audit.status, audit.blockers, audit.summary


def has_recorded_artifact(audit: ValidationReportAudit, candidates: list[Path]) -> bool:
    candidate_set = {candidate.resolve() for candidate in candidates}
    return bool(candidate_set & audit.artifact_paths)


def has_recorded_artifact_role(audit: ValidationReportAudit, roles: set[str], candidates: list[Path]) -> bool:
    candidate_set = {candidate.resolve() for candidate in candidates}
    for role in roles:
        if candidate_set & audit.artifacts_by_role.get(role, set()):
            return True
    return False


def assembly_contract_blockers(
    contact_map: dict[str, object] | None,
    contact_error: str,
    connections: dict[str, object] | None,
    connection_error: str,
    validation_audit: ValidationReportAudit,
) -> list[str]:
    blockers: list[str] = []
    contacts = contact_map.get('contacts') if contact_map else None
    connection_rows = connections.get('connections') if connections else None
    if contact_error:
        blockers.append(f'CONTACT_MAP invalid: {contact_error}')
    elif not isinstance(contacts, list) or not contacts:
        blockers.append('CONTACT_MAP has no contacts')
    if connection_error:
        blockers.append(f'CONNECTIONS invalid: {connection_error}')
    elif not isinstance(connection_rows, list) or not connection_rows:
        blockers.append('CONNECTIONS has no connections')

    for label, rows in [('CONTACT_MAP', contacts), ('CONNECTIONS', connection_rows)]:
        if not isinstance(rows, list):
            continue
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                blockers.append(f'{label} row {index} is not an object')
                continue
            row_id = str(row.get('contact_id') or row.get('connection_id') or index)
            evidence_ids = row.get('evidence_check_ids')
            if not isinstance(evidence_ids, list) or not evidence_ids:
                blockers.append(f'{label} {row_id} has no evidence_check_ids')
                continue
            missing = [
                str(value)
                for value in evidence_ids
                if not isinstance(value, str) or value not in validation_audit.passed_check_ids
            ]
            if missing:
                blockers.append(f'{label} {row_id} evidence_check_ids not passing: {", ".join(missing)}')

    if 'geometry_inspection' not in validation_audit.evidence_types:
        blockers.append('assembly contract has no geometry_inspection evidence in validation_report')
    return blockers


def analyze_completion_gates(
    root: Path,
    milestone: Path,
    python_executable: str | None = None,
    maturity_override: str | None = None,
) -> list[GateResult]:
    gates: list[GateResult] = []
    maturity = milestone_maturity(milestone, maturity_override)
    validation_audit = audit_validation_report(milestone)
    validation_status = validation_audit.status
    validation_blockers = validation_audit.blockers
    validation_summary = validation_audit.summary

    env_checks = cad_toolchain_checks(root, python_executable)
    env_blockers = [check for check in env_checks if check.status == 'ENV_BLOCKED']
    environment_evidence = 'environment' in validation_audit.evidence_types
    gate0_pass = not env_blockers or (validation_status == 'pass' and not validation_blockers and environment_evidence)
    if gate0_pass:
        detail = 'Local CAD environment is available.' if not env_blockers else 'validation_report includes command-backed environment evidence.'
        gates.append(GateResult('Gate 0', 'doctor / environment preflight', 'PASS', detail, []))
    else:
        missing = ', '.join(check.name for check in env_blockers)
        detail = f'ENV_BLOCKED: {missing}'
        if validation_status == 'pass' and not validation_blockers and not environment_evidence:
            detail = f'{detail}; validation_report has no environment evidence check'
        gates.append(
            GateResult(
                'Gate 0',
                'doctor / environment preflight',
                'BLOCKED',
                detail,
                ['Run ./zen-cad doctor --cad-required or record command-backed environment evidence from the CAD runtime used for final artifacts.'],
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
    if source_blockers and maturity == 'final':
        detail = '; '.join(f'{audit.part_id}: {", ".join(audit.blockers[:3])}' for audit in source_blockers[:5])
        steps = [step for audit in source_blockers for step in audit.smallest_unblock_steps]
        gates.append(GateResult('Gate 2', 'standard part source-lock', 'BLOCKED', detail, dedupe_preserving_order(steps)))
    elif source_blockers:
        detail = f'{maturity} maturity allows unresolved source-lock only as generation/layout evidence; final completion remains ineligible.'
        gates.append(GateResult('Gate 2', 'standard part source-lock', 'PASS', detail, []))
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
    source_evidence = has_recorded_artifact_role(validation_audit, {'cad_source', 'source'}, cad_sources)
    export_evidence = has_recorded_artifact_role(
        validation_audit,
        {'primary_step', 'step_export', 'stl_export', 'brep_export', 'cad_export'},
        cad_exports,
    )
    generation_evidence = 'cad_generation' in validation_audit.evidence_types
    if cad_sources and cad_exports and not proxy_only and source_evidence and export_evidence and generation_evidence:
        gates.append(GateResult('Gate 3', 'custom CAD generation', 'PASS', 'custom CAD source and exports have hash-backed generation evidence.', []))
    else:
        details = []
        if not cad_sources:
            details.append('custom CAD source missing')
        if not cad_exports:
            details.append('custom CAD exports missing')
        if proxy_only:
            details.append('custom CAD evidence is proxy-only')
        if cad_sources and not source_evidence:
            details.append('custom CAD source is not recorded with matching validation artifact hash')
        if cad_exports and not export_evidence:
            details.append('custom CAD exports are not recorded with matching validation artifact hashes')
        if not generation_evidence:
            details.append('cad_generation evidence check is missing')
        gates.append(
            GateResult(
                'Gate 3',
                'custom CAD generation',
                'BLOCKED',
                ', '.join(details) or 'custom CAD final evidence missing',
                ['Generate design-specific CAD, record command-backed cad_generation evidence, and hash the source plus final exports.'],
            )
        )

    contact_map, contact_error = read_json_file(milestone / '04_assembly/contact_map.json')
    connections, connection_error = read_json_file(milestone / '04_assembly/connections.json')
    assembly_blockers = assembly_contract_blockers(contact_map, contact_error, connections, connection_error, validation_audit)
    if not assembly_blockers:
        gates.append(GateResult('Gate 4', 'assembly contract', 'PASS', 'CONTACT_MAP and CONNECTIONS are linked to passing geometry evidence checks.', []))
    else:
        gates.append(
            GateResult(
                'Gate 4',
                'assembly contract',
                'BLOCKED',
                '; '.join(assembly_blockers),
                ['Define contact/connection rows with evidence_check_ids that point to passing geometry_inspection or physical validation evidence.'],
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
    standard_parts_present = any(audit.classification in {'off_the_shelf', 'semi_standard_configurable'} for audit in audits)
    metadata_required = maturity == 'final' and standard_parts_present
    final_step_exports = nonempty_artifacts(milestone / '03_cad', {'.step', '.stp'})
    invalid_step_exports = [path for path in final_step_exports if not step_file_has_end_iso(path)]
    recorded_step_exports = has_recorded_artifact_role(validation_audit, STEP_ARTIFACT_ROLES, final_step_exports)
    if (
        (not metadata_required or (not metadata_blocked and normalized_metadata.exists()))
        and (maturity != 'final' or not standard_step_missing)
        and final_step_exports
        and not invalid_step_exports
        and recorded_step_exports
    ):
        gates.append(GateResult('Gate 5', 'export/cache verification', 'PASS', 'STEP cache/metadata and final exports have matching hash evidence.', []))
    else:
        blockers = []
        if metadata_required and (metadata_blocked or not normalized_metadata.exists()):
            blockers.append('normalized STEP metadata is missing or blocked')
        if maturity == 'final' and standard_step_missing:
            blockers.append(f'standard STEP/STP missing for {", ".join(standard_step_missing[:5])}')
        if not final_step_exports:
            blockers.append('final STEP/STP exports are missing')
        if invalid_step_exports:
            blockers.append(f'STEP exports missing END-ISO terminator: {", ".join(path.name for path in invalid_step_exports[:5])}')
        if final_step_exports and not recorded_step_exports:
            blockers.append('final STEP/STP exports are not recorded with matching validation artifact hashes')
        gates.append(
            GateResult(
                'Gate 5',
                'export/cache verification',
                'BLOCKED',
                '; '.join(blockers),
                ['Cache source-backed STEP/STP files, record size/hash evidence, and verify STEP terminators before completion.'],
            )
        )

    if validation_blockers:
        gates.append(
            GateResult(
                'Gate 6',
                'CAD-kernel validation',
                'BLOCKED',
                '; '.join(validation_blockers),
                ['Run command-backed generation, STEP load, and geometry inspection checks; record commands plus hashed artifacts in validation_report.json.'],
            )
        )
    else:
        gates.append(GateResult('Gate 6', 'CAD-kernel validation', 'PASS', 'validation_report has command-backed generation, STEP load, and geometry inspection evidence.', []))

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
    if maturity != 'final':
        gates.append(
            GateResult(
                'Gate 7',
                'final report / BOM / evidence bundle',
                'BLOCKED',
                f'maturity is {maturity!r}, not "final"; concept/layout CAD may be generated but final completion cannot be claimed',
                ['Switch milestone maturity to final only after source-lock, exports, kernel validation, BOM, and report evidence are ready.'],
            )
        )
    elif bom_has_rows and final_report.exists() and validation_status == 'pass' and not report_blocked_language:
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
    audit = audit_validation_report(milestone)
    if audit.blockers:
        return 'BLOCKED', '; '.join(audit.blockers)
    return 'PASS', ''


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='First-run friendly CLI for Zen CAD.')
    parser.add_argument('--root', help='Zen CAD repository root. Defaults to current directory or nearest parent.')
    subparsers = parser.add_subparsers(dest='command', required=True)

    doctor = subparsers.add_parser('doctor', help='Check repo health, schema validation, CoBrA skill sync, and CAD toolchain state.')
    add_root_argument(doctor)
    doctor.add_argument('--cobra-skills-root', help='CoBrA skills root. Defaults to COBRA_SKILLS_ROOT, COBRA_WORKSPACE/skills, or ~/.cobra/workspace/skills.')
    doctor.add_argument('--python', help='Python interpreter to probe. Defaults to ZEN_CAD_PYTHON or the current interpreter.')
    doctor.add_argument('--cad-required', action='store_true', help='Return ENV_BLOCKED when CAD/mesh/kernel tooling is missing; intended for final/release gates, not first CAD pass.')
    doctor.set_defaults(func=command_doctor)

    init = subparsers.add_parser('init', help='Run setup and optionally sync CoBrA skills.')
    add_root_argument(init)
    init.add_argument('--with-cobra', action='store_true', help='Sync bundled Zen CAD skills into CoBrA.')
    init.add_argument('--cobra-skills-root', help='CoBrA skills root. The agentic-cad skill is installed as a child of this directory.')
    init.add_argument('--milestone-request', help='Create a milestone from a natural-language request during init.')
    init.add_argument('--milestone-id', help='Explicit milestone id, e.g. 002_gearbox.')
    init.add_argument('--milestone-title', help='Human-readable title for --milestone-id.')
    init.add_argument('--maturity', choices=sorted(MATURITY_LEVELS), help='Initial maturity for a created milestone. Defaults to concept in scripts/new_milestone.py.')
    init.add_argument('--skip-validation', action='store_true', help='Skip built-in validation during init.')
    init.set_defaults(func=command_init)

    new = subparsers.add_parser('new', help='Create a milestone from a natural-language CAD request.')
    add_root_argument(new)
    new.add_argument('request_words', nargs='*', help='Natural-language CAD request.')
    new.add_argument('--wizard', action='store_true', help='Ask guided first-milestone intake questions.')
    new.add_argument('--id', dest='milestone_id', help='Explicit milestone id, e.g. 002_gearbox.')
    new.add_argument('--title', dest='milestone_title', help='Human-readable title for --id.')
    new.add_argument('--maturity', choices=sorted(MATURITY_LEVELS), default='concept', help='Milestone maturity. concept/layout can generate proxy/layout CAD; final requires completion evidence.')
    new.set_defaults(func=command_new)

    validate = subparsers.add_parser('validate', help='Validate repo/milestone structure and optional completion evidence gates.')
    add_root_argument(validate)
    validate.add_argument('milestones', nargs='*', help='Milestone paths to validate. Defaults to all milestones.')
    validate.add_argument('--level', choices=['all', 'structure', 'completion'], default='all', help='Validation level. all keeps structure exit-code compatibility while printing completion gates.')
    validate.add_argument('--maturity', choices=sorted(MATURITY_LEVELS), help='Override milestone maturity for gate interpretation.')
    validate.add_argument('--python', help='Python interpreter to probe for completion gates. Defaults to ZEN_CAD_PYTHON or the current interpreter.')
    validate.add_argument('--completion-required', action='store_true', help='Return non-zero when validation_report.json does not show completion evidence pass.')
    validate.set_defaults(func=command_validate)

    validate_structure = subparsers.add_parser('validate-structure', help='Validate only required files, schemas, BOM headers, and milestone structure.')
    add_root_argument(validate_structure)
    validate_structure.add_argument('milestones', nargs='*', help='Milestone paths to validate. Defaults to all milestones.')
    validate_structure.set_defaults(func=command_validate_structure)

    validate_completion = subparsers.add_parser('validate-completion', help='Validate completion evidence gates and return non-zero when blocked.')
    add_root_argument(validate_completion)
    validate_completion.add_argument('milestones', nargs='*', help='Milestone paths to validate. Defaults to all milestones.')
    validate_completion.add_argument('--maturity', choices=sorted(MATURITY_LEVELS), help='Override milestone maturity for gate interpretation.')
    validate_completion.add_argument('--python', help='Python interpreter to probe for completion gates. Defaults to ZEN_CAD_PYTHON or the current interpreter.')
    validate_completion.set_defaults(func=command_validate_completion)

    source_lock = subparsers.add_parser('source-lock', help='Audit standard-part source-lock status before CAD generation.')
    add_root_argument(source_lock)
    source_lock.add_argument('milestones', nargs='*', help='Milestone paths to audit. Defaults to all milestones.')
    source_lock.add_argument('--maturity', choices=sorted(MATURITY_LEVELS), help='Override milestone maturity for source-lock severity.')
    source_lock.add_argument('--audit-only', action='store_true', help='Always return zero while printing source-lock blockers.')
    source_lock.set_defaults(func=command_source_lock)

    blocked_report = subparsers.add_parser('blocked-report', help='Render a truthful PASS/BLOCKED evidence report from completion gates.')
    add_root_argument(blocked_report)
    blocked_report.add_argument('milestones', nargs='*', help='Milestone paths to report. Defaults to all milestones.')
    blocked_report.add_argument('--maturity', choices=sorted(MATURITY_LEVELS), help='Override milestone maturity for gate interpretation.')
    blocked_report.add_argument('--python', help='Python interpreter to probe for completion gates. Defaults to ZEN_CAD_PYTHON or the current interpreter.')
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
