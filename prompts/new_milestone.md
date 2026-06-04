# New Milestone Prompt

Create a new legacy Zen CAD milestone for the requested mechanical design only when the user needs the milestone/evidence harness.

For normal Zen CAD 0.8 work, start with `/cad-spec` instead of creating a milestone. If a legacy milestone is required, the user may provide only a CAD goal. Do not ask the user to run a Python command or manually choose a milestone id/title. Internally run this from the Zen CAD repository root:

```bash
python3 scripts/new_milestone.py --request "<goal>"
```

That command derives the next available milestone id and title automatically.

New legacy milestones default to `maturity: concept` and `workflow: /cad-spec`. Generate a useful layout proxy first, mark proxies/envelopes as non-final, and switch to `maturity: final` only when source-lock and validation evidence are ready.

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
