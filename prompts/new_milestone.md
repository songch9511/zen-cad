# New Milestone Prompt

Create a new Zen CAD milestone for the requested mechanical design. Use `scripts/new_milestone.py --id <id> --title <title>` or manually copy `milestones/_template`. Fill the required artifacts progressively and validate with:

```bash
python3 scripts/check_required_files.py .
python3 scripts/check_json_schemas.py .
python3 scripts/validate_milestone.py milestones/<id>
```
