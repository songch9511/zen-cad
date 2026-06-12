#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path


CORE_SKILLS = [
    "cad-spec",
    "assembly-layout",
    "interface-signatures",
    "cad-handoff",
    "cad-replacement",
    "constrained-detail-cad",
]
ROUTER_SKILL = "zen-cad"
ALL_INSTALLED_SKILLS = [ROUTER_SKILL, *CORE_SKILLS]

RUNTIME_BINDING_HEADING = "## CoBrA Runtime Binding"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Install Zen CAD skills into a local CoBrA workspace."
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="Zen CAD repository root. Defaults to this script's parent repository.",
    )
    parser.add_argument(
        "--cobra-home",
        type=Path,
        default=Path(os.environ.get("COBRA_HOME", "~/.cobra")).expanduser(),
        help="CoBrA home directory. Defaults to $COBRA_HOME or ~/.cobra.",
    )
    parser.add_argument(
        "--skills-dir",
        type=Path,
        help="CoBrA skills directory. Defaults to <cobra-home>/workspace/skills.",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        help="Backup directory for replaced skills. Defaults to <cobra-home>/backups/zen-cad-skill-install-<timestamp>.",
    )
    parser.add_argument(
        "--with-cad-deps",
        action="store_true",
        help="Create/update a repo-local virtualenv and install build123d for local STEP generation.",
    )
    parser.add_argument(
        "--python",
        default="",
        help="Python executable used to create the CAD virtualenv. Defaults to python3.11 when available, otherwise the current interpreter.",
    )
    parser.add_argument(
        "--venv",
        type=Path,
        help="Virtualenv path for CAD dependencies. Defaults to <repo-root>/.venv.",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not back up existing installed Zen CAD skill directories before replacing them.",
    )
    parser.add_argument(
        "--skip-validate",
        action="store_true",
        help="Skip running tools/validate_contract.py after skill installation.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the planned installation without writing files or installing dependencies.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    repo_root = args.repo_root.expanduser().resolve()
    cobra_home = args.cobra_home.expanduser().resolve()
    skills_dir = (
        args.skills_dir.expanduser().resolve()
        if args.skills_dir
        else cobra_home / "workspace" / "skills"
    )
    backup_dir = (
        args.backup_dir.expanduser().resolve()
        if args.backup_dir
        else cobra_home / "backups" / f"zen-cad-skill-install-{timestamp()}"
    )
    venv_dir = (
        args.venv.expanduser().resolve()
        if args.venv
        else repo_root / ".venv"
    )
    prefer_venv = args.with_cad_deps or (venv_dir / "bin" / "python").exists()

    errors = validate_repo(repo_root)
    if errors:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 2

    print(f"Zen CAD repo: {repo_root}")
    print(f"CoBrA skills: {skills_dir}")
    print(f"Install skills: {', '.join('/' + name for name in ALL_INSTALLED_SKILLS)}")
    if not args.no_backup:
        print(f"Backup dir: {backup_dir}")
    if args.with_cad_deps:
        print(f"CAD venv: {venv_dir}")

    if args.dry_run:
        print("Dry run only; no files changed.")
        return 0

    skills_dir.mkdir(parents=True, exist_ok=True)
    if not args.no_backup:
        backup_existing_skills(skills_dir, backup_dir)

    install_router_skill(skills_dir / ROUTER_SKILL, repo_root, venv_dir, prefer_venv)
    for slug in CORE_SKILLS:
        install_core_skill(repo_root, skills_dir, slug, venv_dir, prefer_venv)

    if args.with_cad_deps:
        python = select_python(args.python)
        sys.stdout.flush()
        install_cad_dependencies(python, venv_dir)

    if not args.skip_validate:
        code = run_contract_validation(repo_root, venv_dir)
        if code != 0:
            print("warning: contract validation failed; inspect output above", file=sys.stderr)
            return code

    print("CoBrA install complete.")
    print("Start a new CoBrA chat or refresh the skill picker, then use /zen-cad or /cad-spec.")
    return 0


def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S")


def validate_repo(repo_root: Path) -> list[str]:
    errors: list[str] = []
    required = [
        repo_root / "skills",
        repo_root / "schemas",
        repo_root / "registry",
        repo_root / "tools" / "validate_contract.py",
    ]
    for path in required:
        if not path.exists():
            errors.append(f"missing required path: {path}")
    for slug in CORE_SKILLS:
        skill = repo_root / "skills" / slug / "SKILL.md"
        if not skill.is_file():
            errors.append(f"missing skill: {skill}")
    return errors


def backup_existing_skills(skills_dir: Path, backup_dir: Path) -> None:
    copied = 0
    for slug in ALL_INSTALLED_SKILLS:
        existing = skills_dir / slug
        if not existing.exists():
            continue
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(existing, backup_dir / slug, dirs_exist_ok=True)
        copied += 1
    if copied:
        print(f"Backed up {copied} existing skill(s).")


def install_core_skill(repo_root: Path, skills_dir: Path, slug: str, venv_dir: Path, prefer_venv: bool) -> None:
    source = repo_root / "skills" / slug
    target = skills_dir / slug
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target, ignore=shutil.ignore_patterns(".DS_Store", "__pycache__"))
    inject_runtime_binding(target / "SKILL.md", slug)
    write_workspace_binding(target / "ZEN_CAD_WORKSPACE.md", repo_root, venv_dir, prefer_venv)
    print(f"Installed /{slug}")


def install_router_skill(target: Path, repo_root: Path, venv_dir: Path, prefer_venv: bool) -> None:
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    (target / "SKILL.md").write_text(router_skill_text(), encoding="utf-8")
    write_workspace_binding(target / "ZEN_CAD_WORKSPACE.md", repo_root, venv_dir, prefer_venv)
    print(f"Installed /{ROUTER_SKILL}")


def inject_runtime_binding(skill_md: Path, slug: str) -> None:
    text = skill_md.read_text(encoding="utf-8")
    if RUNTIME_BINDING_HEADING in text:
        return
    h1 = f"# {title_from_slug(slug)}"
    section = (
        f"{h1}\n\n"
        f"{RUNTIME_BINDING_HEADING}\n\n"
        "When this skill is installed in CoBrA, first read the sibling "
        "`ZEN_CAD_WORKSPACE.md` file if present. Use its `Repository root:` "
        "value as the Zen CAD repository root unless the user explicitly "
        "provides another root. Resolve repo-level paths such as `schemas/`, "
        "`registry/`, `tools/`, `viewer/`, `benchmarks/`, and `work/` relative "
        f"to that repository root, not relative to the CoBrA skill directory for `/{slug}`.\n"
    )
    if h1 in text:
        text = text.replace(h1, section, 1)
    else:
        text = f"{section}\n{text}"
    skill_md.write_text(text, encoding="utf-8")


def title_from_slug(slug: str) -> str:
    return {
        "cad-spec": "CAD Spec",
        "assembly-layout": "Assembly Layout",
        "interface-signatures": "Interface Signatures",
        "cad-handoff": "CAD Handoff",
        "cad-replacement": "CAD Replacement",
        "constrained-detail-cad": "Constrained Detail CAD",
    }.get(slug, slug.replace("-", " ").title())


def router_skill_text() -> str:
    routes = "\n".join(
        [
            "- Use `/cad-spec` for new mechanical part or assembly requests.",
            "- Use `/assembly-layout` when the task is only about frames, datums, axes, contacts, joints, clearances, or proceed review.",
            "- Use `/interface-signatures` when a layout needs standard component interface facts before full supplier geometry.",
            "- Use `/cad-handoff` when a CAD-native spec should become a generation, inspection, repair, or downstream handoff brief.",
            "- Use `/cad-replacement` when a layout proxy part should be replaced while preserving locked facts.",
            "- Use `/constrained-detail-cad` when a custom part should take on a requested shape while preserving protected interface frames, datums, clearances, bores, shafts, bolt patterns, and motion envelopes.",
        ]
    )
    return f"""---
name: zen-cad
description: Entry point for the installed songch9511/zen-cad workflow in CoBrA. Use for mechanical CAD requests, then route to /cad-spec, /assembly-layout, /interface-signatures, /cad-handoff, /cad-replacement, or /constrained-detail-cad as needed.
version: 1.1.0
---

# Zen CAD

## CoBrA Runtime Binding

First read the sibling `ZEN_CAD_WORKSPACE.md` file. Use its `Repository root:` value as the Zen CAD repository root unless the user explicitly provides another root. Resolve repo-level paths such as `schemas/`, `registry/`, `tools/`, `viewer/`, `benchmarks/`, and `work/` relative to that repository root, not relative to the CoBrA skill directory.

## Purpose

Use this as the CoBrA entry point for the installed `songch9511/zen-cad` skill pack.

Default route:

{routes}

## Workflow

1. Read `ZEN_CAD_WORKSPACE.md` and confirm the repository root exists.
2. Select the narrowest matching Zen CAD skill from the route list above.
3. Read that skill's `SKILL.md` and only the relevant reference files it names.
4. For repo-level schemas, registry files, tools, viewer assets, or benchmark packages, use paths under the repository root.
5. For local contract checks, prefer the Python command in `ZEN_CAD_WORKSPACE.md`.
6. For local build123d generation, use the pipeline command shape in `ZEN_CAD_WORKSPACE.md`.

## Hard Rules

- Do not run obsolete wrapper commands unless that executable exists in the selected repository root.
- Do not treat the CoBrA skill directory as the Zen CAD repository root.
- Do not skip the routed skill's reference files when the task depends on their contract details.
"""


def write_workspace_binding(path: Path, repo_root: Path, venv_dir: Path, prefer_venv: bool) -> None:
    python_cmd = python_command(repo_root, venv_dir, prefer_venv)
    text = f"""# Zen CAD Workspace Binding

Repository root: {repo_root}
Source repository: https://github.com/songch9511/zen-cad
Installed for CoBrA skills: {", ".join("/" + name for name in ALL_INSTALLED_SKILLS)}

When a Zen CAD skill runs in CoBrA, use the repository root above as the Zen CAD workspace unless the user explicitly provides a different root. The CoBrA skill directory contains installed skill docs; it is not the Zen CAD repository root.

Resolve these paths relative to the repository root:

- `schemas/`
- `registry/`
- `tools/`
- `viewer/`
- `benchmarks/`
- `work/`

Useful local checks:

```bash
cd "<repository-root>" && {python_cmd} tools/validate_contract.py
cd "<repository-root>" && {python_cmd} -m unittest discover -s tests
```

Useful local generation command shape:

```bash
cd "<repository-root>" && {python_cmd} tools/run_contract_pipeline.py --package <contract-package> --out <run-dir> --target-harness build123d
```
"""
    path.write_text(text, encoding="utf-8")


def python_command(repo_root: Path, venv_dir: Path, prefer_venv: bool) -> str:
    if not prefer_venv:
        return "python3"
    try:
        rel = venv_dir.relative_to(repo_root)
    except ValueError:
        return f'"{venv_dir / "bin" / "python"}"'
    return str(rel / "bin" / "python")


def select_python(requested: str) -> str:
    if requested:
        return requested
    python311 = shutil.which("python3.11")
    return python311 or sys.executable


def install_cad_dependencies(python: str, venv_dir: Path) -> None:
    print(f"Creating/updating CAD virtualenv with {python}", flush=True)
    subprocess.run([python, "-m", "venv", str(venv_dir)], check=True)
    venv_python = venv_dir / "bin" / "python"
    subprocess.run([str(venv_python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([str(venv_python), "-m", "pip", "install", "build123d"], check=True)


def run_contract_validation(repo_root: Path, venv_dir: Path) -> int:
    python = venv_dir / "bin" / "python"
    if not python.exists():
        python = Path(sys.executable)
    print("Running contract validation...", flush=True)
    completed = subprocess.run([str(python), "tools/validate_contract.py"], cwd=repo_root)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
