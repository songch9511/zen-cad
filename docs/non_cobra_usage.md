# Non-CoBrA Usage

Zen CAD can be used in any agentic environment that can read Markdown, edit files, run scripts, and create CAD artifacts. Treat `skills/agentic-cad/SKILL.md` as the main operating manual and the files in `prompts/` as task entrypoints.

## Claude Code, Codex, Cursor, or similar tools

Clone or download the Zen CAD repo, open it as the project root, and run:

```bash
./zen-cad doctor
```

Then tell the agent what you want to build in natural language, for example:

```text
기어 박스를 만들고 싶어
```

The expected agent behavior is prompt-first milestone startup: do not ask the user to run a milestone command or choose an id/title. The agent should internally run `python3 scripts/new_milestone.py --request "<goal>"`, create the next milestone such as `002_gearbox` titled `Gearbox`, then use `prompts/new_milestone.md` for the active milestone and keep validation evidence in the milestone folder.

For manual use, the same flow is available through the repo-local wrapper:

```bash
./zen-cad new "기어 박스를 만들고 싶어"
./zen-cad validate milestones/002_gearbox
```

For automation or scripted startup, `./zen-cad init --milestone-request "<goal>"` and `scripts/setup_zen_cad.py --milestone-request "<goal>"` are both available. When an exact folder name must be pinned, explicit `--milestone-id` and `--milestone-title` still work.

CoBrA-only skill installation is not required in Claude Code or Codex because the skill file is already inside this repository.
