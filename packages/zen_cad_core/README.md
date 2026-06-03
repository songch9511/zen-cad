# Zen CAD Core

Zen CAD Core is the machine-checkable part of the workflow: schemas, milestone templates, source-lock audits, completion gates, and release evidence checks.

In 0.6.x this is a documented package boundary, not a separate published Python package yet. The implementation remains repo-local so existing users can keep running the same commands:

- `scripts/zen_cad.py` for the `./zen-cad` CLI
- `scripts/new_milestone.py` for prompt-first milestone creation
- `scripts/check_required_files.py` and `scripts/check_json_schemas.py` for structure validation
- `schemas/`, `templates/`, and `checklists/` for the artifact contract

The core intentionally does not own CAD kernels, web search, catalog retrieval, or multi-agent execution. Those belong to the harness and external CAD/tooling layer.
