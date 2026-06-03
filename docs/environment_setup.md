# Environment Setup

Minimum requirements:

- Python 3.10+
- no required third-party Python package for structure/schema metadata validation
- numpy and trimesh for mesh/loadability validation
- CadQuery, OpenSCAD, or another project-approved CAD kernel/export path for final CAD work
- a CAD generator/exporter appropriate to the task
- bundled schema validation for required keys, types, enums, arrays, object structure, and BOM headers

## One-command setup

Run this setup check with the Zen CAD repository as the command cwd:

```bash
./zen-cad doctor
```

`doctor` validates required files, checks bundled JSON/CSV artifacts, reports CoBrA skill discovery/workspace binding state, and shows CAD toolchain preflight. If you only need structure validation, missing CAD tooling is reported as `ENV_BLOCKED` but the repository can still be workflow-ready.

Before final CAD generation or completion validation, use:

```bash
./zen-cad doctor --cad-required
```

When CoBrA workers do not use the same Python as your terminal, pass the working CAD venv explicitly:

```bash
./zen-cad doctor --cad-required --python /path/to/.venv/bin/python
```

If this exits `ENV_BLOCKED`, do not spend the whole project repairing the local environment before any CAD exists. For concept/layout work, continue with the harness's available CAD path and record the strict-env blocker separately. Only final/release claims require resolving this preflight.

To run setup explicitly, use:

```bash
./zen-cad init
```

The setup helper validates required files, checks bundled JSON/CSV artifacts, and validates every milestone skeleton under `milestones/`.

For CoBrA, add `--with-cobra` to copy the bundled Zen CAD skills into the CoBrA skills directory before validation.

```bash
./zen-cad init --with-cobra
```

Skill sync writes a `ZEN_CAD_WORKSPACE.md` binding beside each installed skill. It does not change the CoBrA process working directory. Do not use the Zen CAD repository as the CoBrA daemon cwd; start or restart CoBrA from its normal installation, then let installed skills read the workspace binding and run Zen CAD commands with that root as cwd or `--root`.

Interpret blockers by layer:

- Missing CoBrA skills or missing `ZEN_CAD_WORKSPACE.md`: rerun `./zen-cad init --with-cobra`.
- Missing `numpy`, `trimesh`, `build123d`, OCP, or CadQuery: strict final CAD evidence cannot run in that Python. This does not block CoBrA skill discovery or concept/layout CAD generation.

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
