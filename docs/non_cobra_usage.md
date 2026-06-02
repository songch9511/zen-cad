# Non-CoBrA Usage

Zen CAD can be used in any agentic environment that can read Markdown, edit files, run scripts, and create CAD artifacts. Treat `skills/agentic-cad/SKILL.md` as the main operating manual and the files in `prompts/` as task entrypoints.

## Claude Code, Codex, Cursor, or similar tools

Clone or download the Zen CAD repo, open it as the project root, and run:

```bash
python3 scripts/setup_zen_cad.py
```

To create the first CAD job folder immediately, replace the milestone id and title with your actual target:

```bash
python3 scripts/setup_zen_cad.py \
  --milestone-id 002_foldable_drone_landing_gear \
  --milestone-title "Foldable drone landing gear"
```

The job is not limited to the example shown here. Use any unique lowercase snake_case milestone id, such as `002_gearbox_stage`, `002_watch_escapement`, `002_robot_arm_joint`, `002_camera_mount`, or `002_desktop_cnc_fixture`.

Then tell the agent:

```text
Use this repository as the Zen CAD workspace. Read README.md and skills/agentic-cad/SKILL.md first. Use prompts/new_milestone.md for the active milestone and keep validation evidence in the milestone folder.
```

CoBrA-only skill installation is not required in Claude Code or Codex because the skill file is already inside this repository.
