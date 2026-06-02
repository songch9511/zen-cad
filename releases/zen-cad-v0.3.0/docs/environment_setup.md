# Environment Setup

Minimum requirements:

- Python 3.10+
- no required third-party Python package for metadata validation
- a CAD generator/exporter appropriate to the task
- optional JSON Schema package for stricter schema checks; the bundled script includes fallback validation for required fields and object structure

## One-command setup

Run this from the Zen CAD repository root:

```bash
python3 scripts/setup_zen_cad.py
```

The setup helper validates required files, checks bundled JSON/CSV artifacts, validates the milestone template, and validates the reference milestone.

For CoBrA, add `--sync-cobra-skill` to copy `skills/agentic-cad/SKILL.md` into `~/.cobra/workspace/skills/agentic-cad/SKILL.md` before validation.

```bash
python3 scripts/setup_zen_cad.py --sync-cobra-skill
```

After that, milestone startup is prompt-first: the user can type a natural CAD goal such as `기어 박스를 만들고 싶어` in the agent prompt, and the agent should internally run `python3 scripts/new_milestone.py --request "<goal>"` to create the next milestone, for example `002_gearbox` titled `Gearbox`.

For automation, CI, or non-interactive setup, the helper can still create a first milestone during setup from a natural-language request:

```bash
python3 scripts/setup_zen_cad.py \
  --milestone-request "기어 박스를 만들고 싶어"
```

The explicit id/title path also remains available when you must pin an exact folder name:

```bash
python3 scripts/setup_zen_cad.py \
  --milestone-id 002_desktop_cnc_fixture \
  --milestone-title "Desktop CNC workholding fixture"
```

The milestone can be a gearbox stage, robot arm joint, watch mechanism, drone frame, enclosure, fixture, actuator, or any other CAD job. The examples are not presets.
