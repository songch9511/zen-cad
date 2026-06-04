# Zen CAD Core

Zen CAD Core is the machine-checkable legacy evidence layer: schemas, milestone templates, source-lock audits, completion gates, artifact hash checks, and release evidence checks.

In 0.8.0 this is still a documented package boundary, not a separate published Python package. The implementation remains repo-local so existing users can keep running the same commands:

- `scripts/zen_cad.py` for the `./zen-cad` CLI
- `scripts/new_milestone.py` for legacy milestone creation
- `scripts/check_required_files.py` and `scripts/check_json_schemas.py` for structure validation
- `schemas/`, `templates/`, and `checklists/` for the artifact contract

The core intentionally does not own CAD kernels, web search, catalog retrieval, spec writing, or multi-agent execution. Those belong to the focused skills, harness, and external CAD/tooling layer.
