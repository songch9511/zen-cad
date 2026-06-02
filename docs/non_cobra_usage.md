# Non-CoBrA Usage

Zen CAD can be used in any agentic environment that can read Markdown, edit files, run scripts, and create CAD artifacts. Treat `skills/agentic-cad/SKILL.md` as the main operating manual and the files in `prompts/` as task entrypoints.

## Claude Code, Codex, Cursor, or similar tools

Clone or download the Zen CAD repo, open it as the project root, and run:

```bash
python3 scripts/setup_zen_cad.py
```

To create the first CAD job folder immediately:

```bash
python3 scripts/setup_zen_cad.py \
  --milestone-id 002_robot_gripper \
  --milestone-title "Small servo-driven robot gripper"
```

Then tell the agent:

```text
Use this repository as the Zen CAD workspace. Read README.md and skills/agentic-cad/SKILL.md first. Use prompts/new_milestone.md for the active milestone and keep validation evidence in the milestone folder.
```

CoBrA-only skill installation is not required in Claude Code or Codex because the skill file is already inside this repository.
