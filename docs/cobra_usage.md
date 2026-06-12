# CoBrA Usage

Zen CAD can be installed into CoBrA as workspace skills. The installer copies the core Zen CAD skill pack into the local CoBrA workspace, writes a `ZEN_CAD_WORKSPACE.md` binding beside each installed skill, and optionally prepares a repo-local Python virtualenv for build123d STEP generation.

## Quickstart

```bash
git clone https://github.com/songch9511/zen-cad.git
cd zen-cad
python3 tools/install_cobra.py --with-cad-deps
```

After installation, start a new CoBrA chat or refresh the skill picker. Use:

```text
/zen-cad create a NEMA17 mount plate
```

or route directly:

```text
/cad-spec create a GT2 belt driven linear slide
```

## What Gets Installed

The installer writes these workspace skills:

- `/zen-cad`
- `/cad-spec`
- `/assembly-layout`
- `/interface-signatures`
- `/cad-handoff`
- `/cad-replacement`
- `/constrained-detail-cad`

By default, the target directory is:

```text
~/.cobra/workspace/skills
```

Existing installed Zen CAD skill directories are backed up under:

```text
~/.cobra/backups/zen-cad-skill-install-<timestamp>
```

## Spec-Only Install

If you only want the skills and contract workflow, skip CAD dependencies:

```bash
python3 tools/install_cobra.py
```

This is enough for spec, layout, replacement planning, constrained detail planning, and downstream handoff prompts. Local build123d STEP generation requires `--with-cad-deps`.

## Custom Paths

Use a separate CoBrA home or skills directory when testing:

```bash
python3 tools/install_cobra.py --cobra-home /tmp/cobra-home
python3 tools/install_cobra.py --skills-dir /tmp/cobra-home/workspace/skills
```

Use a specific Python for CAD dependencies:

```bash
python3 tools/install_cobra.py --with-cad-deps --python /opt/homebrew/bin/python3.11
```

Preview changes without writing:

```bash
python3 tools/install_cobra.py --dry-run
```

## Verification

The installer runs the contract validator unless `--skip-validate` is passed. For a full local check after installing CAD dependencies:

```bash
.venv/bin/python tools/validate_contract.py
.venv/bin/python -m unittest discover -s tests
```

For build123d generation from an existing contract package:

```bash
.venv/bin/python tools/run_contract_pipeline.py --package <contract-package> --out <run-dir> --target-harness build123d
```

## Troubleshooting

If CoBrA does not show the skills, refresh the skill picker or start a new chat. CoBrA scans `~/.cobra/workspace/skills/<slug>/SKILL.md`.

If local generation reports `build123d import failed`, run:

```bash
python3 tools/install_cobra.py --with-cad-deps
```

If a skill resolves repo paths incorrectly, open the installed skill directory and check `ZEN_CAD_WORKSPACE.md`. Its `Repository root:` line should point to this Zen CAD checkout.
