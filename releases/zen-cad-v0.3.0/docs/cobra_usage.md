# CoBrA Usage

From the Zen CAD repository root, run:

```bash
python3 scripts/setup_zen_cad.py --sync-cobra-skill
```

That command copies the embedded `/agentic-cad` skill from `skills/agentic-cad/SKILL.md` to `~/.cobra/workspace/skills/agentic-cad/SKILL.md` and runs the bundled validation checks.

To create a new CAD job at the same time:

```bash
python3 scripts/setup_zen_cad.py \
  --sync-cobra-skill \
  --milestone-id 002_robot_gripper \
  --milestone-title "Small servo-driven robot gripper"
```

Then start from `prompts/project_kickoff.md` for a new workspace or `prompts/new_milestone.md` for a new CAD job. Keep standard parts source-first and custom geometry generate-second. Require `scripts/check_required_files.py`, `scripts/check_json_schemas.py`, and `scripts/validate_milestone.py` evidence before reporting completion.
