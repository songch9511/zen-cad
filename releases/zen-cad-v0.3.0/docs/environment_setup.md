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

To create a first milestone during setup:

```bash
python3 scripts/setup_zen_cad.py \
  --milestone-id 002_robot_gripper \
  --milestone-title "Small servo-driven robot gripper"
```

For CoBrA, add `--sync-cobra-skill` to copy `skills/agentic-cad/SKILL.md` into `~/.cobra/workspace/skills/agentic-cad/SKILL.md` before validation.

```bash
python3 scripts/setup_zen_cad.py \
  --sync-cobra-skill \
  --milestone-id 002_robot_gripper \
  --milestone-title "Small servo-driven robot gripper"
```
