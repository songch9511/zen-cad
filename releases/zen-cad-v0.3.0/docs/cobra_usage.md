# CoBrA Usage

From the Zen CAD repository root, run:

```bash
python3 scripts/setup_zen_cad.py --sync-cobra-skill
```

That command copies the embedded `/agentic-cad` skill from `skills/agentic-cad/SKILL.md` to `~/.cobra/workspace/skills/agentic-cad/SKILL.md` and runs the bundled validation checks.

To create a new CAD job at the same time, replace the milestone id and title with your actual target:

```bash
python3 scripts/setup_zen_cad.py \
  --sync-cobra-skill \
  --milestone-id 002_robot_arm_joint \
  --milestone-title "Compact robot arm shoulder joint"
```

The job is not limited to the example shown here. Use any unique lowercase snake_case milestone id, such as `002_gearbox_stage`, `002_watch_escapement`, `002_drone_frame`, `002_camera_mount`, or `002_desktop_cnc_fixture`.

Then start from `prompts/project_kickoff.md` for a new workspace or `prompts/new_milestone.md` for a new CAD job. Keep standard parts source-first and custom geometry generate-second. Require `scripts/check_required_files.py`, `scripts/check_json_schemas.py`, and `scripts/validate_milestone.py` evidence before reporting completion.
