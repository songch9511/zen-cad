# Environment Setup

Minimum requirements:

- Python 3.10+
- no required third-party Python package for structure/schema metadata validation
- numpy and trimesh for mesh/loadability validation
- CadQuery, OpenSCAD, or another project-approved CAD kernel/export path for final CAD work
- a CAD generator/exporter appropriate to the task
- bundled schema validation for required keys, types, enums, arrays, object structure, and BOM headers

## One-command setup

Run this from the Zen CAD repository root:

```bash
./zen-cad doctor
```

`doctor` validates required files, checks bundled JSON/CSV artifacts, reports CoBrA skill sync state, and shows CAD toolchain preflight. If you only need structure validation, missing CAD tooling is reported as `ENV_BLOCKED` but the repository can still be workflow-ready.

Before final CAD generation or completion validation, use:

```bash
./zen-cad doctor --cad-required
```

When CoBrA workers do not use the same Python as your terminal, pass the working CAD venv explicitly:

```bash
./zen-cad doctor --cad-required --python /path/to/.venv/bin/python
```

If this exits `ENV_BLOCKED`, stop CAD generation and resolve the missing toolchain first. A truthful blocked report is preferred over proxy CAD that looks complete.

To run setup explicitly, use:

```bash
./zen-cad init
```

The setup helper validates required files, checks bundled JSON/CSV artifacts, and validates every milestone skeleton under `milestones/`.

For CoBrA, add `--with-cobra` to copy the bundled `/agentic-cad`, `/spec-to-cad`, and `/self-evolving-producer-verifier` skills into the CoBrA skills directory before validation.

```bash
./zen-cad init --with-cobra
```

Skill sync does not register the Zen CAD repository as the active CoBrA workspace. Start CoBrA from the Zen CAD repository root, or explicitly point the agent to this repository path.

After that, milestone startup is prompt-first: the user can type a natural CAD goal such as `기어 박스를 만들고 싶어` in the agent prompt, and the agent should internally run `python3 scripts/new_milestone.py --request "<goal>"` to create the next milestone, for example `003_gearbox` titled `Gearbox` in this repository.

For automation, CI, or non-interactive setup, the helper can still create a first milestone during setup from a natural-language request:

```bash
./zen-cad init \
  --milestone-request "기어 박스를 만들고 싶어"
```

The explicit id/title path also remains available when you must pin an exact folder name:

```bash
./zen-cad init \
  --milestone-id 002_desktop_cnc_fixture \
  --milestone-title "Desktop CNC workholding fixture"
```

The milestone can be a gearbox stage, robot arm joint, watch mechanism, drone frame, enclosure, fixture, actuator, or any other CAD job. The examples are not presets.
