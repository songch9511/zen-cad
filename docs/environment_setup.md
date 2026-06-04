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

`doctor` validates required files, checks bundled JSON/CSV artifacts, and shows CAD toolchain preflight. If you only need structure validation, missing CAD tooling is reported as `ENV_BLOCKED` but the repository can still be workflow-ready.

Before final CAD generation or completion validation, use:

```bash
./zen-cad doctor --cad-required
```

When the active CAD runtime does not use the same Python as your terminal, pass the working CAD venv explicitly:

```bash
./zen-cad doctor --cad-required --python /path/to/.venv/bin/python
```

If this exits `ENV_BLOCKED`, do not spend the whole project repairing the local environment before any CAD exists. For concept/layout work, continue with the harness's available CAD path and record the strict-env blocker separately. Only final/release claims require resolving this preflight.

To run setup explicitly, use:

```bash
./zen-cad init
```

The setup helper validates required files, checks bundled JSON/CSV artifacts, and validates every legacy milestone skeleton under `milestones/`.

Interpret blockers by layer:

- Missing required repository files or invalid schemas: fix the repo before claiming workflow readiness.
- Missing `numpy`, `trimesh`, `build123d`, OCP, or CadQuery: strict final CAD evidence cannot run in that Python. This does not block concept/layout spec work.

After that, new CAD work should start with `/cad-spec`. Write a CAD-native spec first, then use `/cad-handoff` to ask the active CAD harness for a low-detail layout proxy.

For legacy milestone automation, CI, or final-evidence experiments, the helper can still create a first milestone during setup from a natural-language request:

```bash
./zen-cad init \
  --milestone-request "<goal>"
```

The explicit id/title path also remains available when you must pin an exact folder name:

```bash
./zen-cad init \
  --milestone-id 002_desktop_cnc_fixture \
  --milestone-title "Desktop CNC workholding fixture"
```

The legacy milestone can be any CAD job. It is not the default 0.8 user experience; use it only when you need the milestone/evidence harness.
