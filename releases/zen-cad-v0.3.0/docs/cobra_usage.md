# CoBrA Usage

From the Zen CAD repository root, run setup once:

```bash
python3 scripts/setup_zen_cad.py --sync-cobra-skill
```

That command copies the embedded `/agentic-cad` skill from `skills/agentic-cad/SKILL.md` to `~/.cobra/workspace/skills/agentic-cad/SKILL.md` and runs the bundled validation checks.

## Prompt-first milestone startup

After setup, the user does not need to run another Python command to create a CAD job. In a new CoBrA session or prompt window, the user can simply type a natural-language CAD goal such as:

```text
기어 박스를 만들고 싶어
```

The agent should treat that prompt as the milestone creation request. Do not ask the user to run a Python command, and do not require the user to manually choose a milestone id/title. Internally run this command from the Zen CAD repository root:

```bash
python3 scripts/new_milestone.py --request "<goal>"
```

For example, `기어 박스를 만들고 싶어` should create the next available milestone such as `002_gearbox` with title `Gearbox`. Then follow `prompts/new_milestone.md`, keep standard parts source-first and custom geometry generate-second, and require `scripts/check_required_files.py`, `scripts/check_json_schemas.py`, and `scripts/validate_milestone.py` evidence before reporting completion.

The setup helper still supports `--milestone-request` for automation or smoke tests, and explicit `--milestone-id` plus `--milestone-title` still works when an exact folder name must be pinned.
