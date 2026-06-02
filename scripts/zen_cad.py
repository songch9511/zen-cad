#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
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

    checks = [
        CheckResult('Repository root', 'PASS', 'Zen CAD files detected'),
        CheckResult('Python runtime', 'PASS' if sys.version_info >= (3, 10) else 'WARN', 'Python 3.10+ recommended'),
        run_required_file_check(root),
        run_schema_check(root),
        check_cobra_skills(skills_root),
    ]

    print_section('Checks')
    for check in checks:
        print_check(check)

    blocked = [check for check in checks if check.status == 'BLOCKED']
    print_section('CoBrA workspace note')
    print('CoBrA skill sync installs the workflow skills only.')
    print('It does not register this repository as the active CoBrA workspace.')
    print(f'Start CoBrA from this repo, or explicitly point the agent to: {root}')

    if blocked:
        print_section('Zen CAD doctor: BLOCKED')
        print('Smallest unblock step:')
        print(f'- Run: {sys.executable} scripts/setup_zen_cad.py')
        return 1

    print_section('Zen CAD doctor: PASS')
    print('Next:')
    print('- Create a CAD milestone: ./zen-cad new "기어 박스를 만들고 싶어"')
    print('- Validate a milestone: ./zen-cad validate milestones/<id>')
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
    evidence_blocked: list[tuple[Path, str]] = []
    for milestone in targets:
        result = validate_single_milestone(root, milestone)
        if result.returncode != 0:
            blocked_milestones.append(milestone)
            print_section(f'Milestone: {milestone.name}')
            print('[BLOCKED] Milestone structure')
            print(first_line(result.stdout or result.stderr))
            continue
        print_milestone_summary(root, milestone)
        completion_status, reason = completion_evidence_status(milestone)
        if completion_status != 'PASS':
            evidence_blocked.append((milestone, reason))

    if blocked_milestones:
        print_section('Zen CAD validation result: BLOCKED')
        print('Reason:')
        for milestone in blocked_milestones:
            print(f'- {milestone.relative_to(root)} did not pass structure validation')
        return 1

    print_section('Zen CAD validation result: PASS')
    print('Scope: required files, JSON schemas, BOM headers, and milestone structure.')
    if evidence_blocked:
        print('\nCompletion evidence: BLOCKED')
        print('Reason:')
        for milestone, reason in evidence_blocked:
            print(f'- {milestone.relative_to(root)}: {reason}')
        print('Smallest unblock step:')
        print('- Run /spec-to-cad or equivalent CAD tooling, then update validation_report.json with reproducible CAD/export evidence.')
        if args.completion_required:
            return 2
    else:
        print('Completion evidence: PASS')
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

    doctor = subparsers.add_parser('doctor', help='Check repo health, schema validation, and CoBrA skill sync state.')
    add_root_argument(doctor)
    doctor.add_argument('--cobra-skills-root', help='CoBrA skills root. Defaults to COBRA_SKILLS_ROOT, COBRA_WORKSPACE/skills, or ~/.cobra/workspace/skills.')
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

    validate = subparsers.add_parser('validate', help='Validate repo and milestone evidence structure.')
    add_root_argument(validate)
    validate.add_argument('milestones', nargs='*', help='Milestone paths to validate. Defaults to all milestones.')
    validate.add_argument('--completion-required', action='store_true', help='Return non-zero when validation_report.json does not show completion evidence pass.')
    validate.set_defaults(func=command_validate)
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
