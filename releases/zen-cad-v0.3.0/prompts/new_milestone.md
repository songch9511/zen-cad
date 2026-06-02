# New Milestone Prompt

Create a new Zen CAD milestone for the requested mechanical design.

For prompt-first milestone startup, the user may only provide a CAD goal such as `기어 박스를 만들고 싶어`. Do not ask the user to run a Python command or manually choose a milestone id/title. Internally run this from the Zen CAD repository root:

```bash
python3 scripts/new_milestone.py --request "<goal>"
```

That command derives the next available milestone id and title automatically, for example `002_gearbox` and `Gearbox`.

For automation or exact naming, the existing explicit path still works:

```bash
python3 scripts/new_milestone.py --id <id> --title <title>
```

Fill the required artifacts progressively and validate with:

```bash
python3 scripts/check_required_files.py .
python3 scripts/check_json_schemas.py .
python3 scripts/validate_milestone.py milestones/<id>
```
