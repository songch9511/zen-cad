# CoBrA Usage

From the Zen CAD repository root, run setup once:

```bash
./zen-cad init --with-cobra
```

That command syncs the bundled Zen CAD skills into the CoBrA skills directory and runs the bundled validation checks. The installed skills include `/agentic-cad`, `/source-step-parts`, `/spec-to-cad`, `/mechanism-kinematics`, `/cad-artifact-reviewer`, `/manufacturing-preflight`, and `/self-evolving-producer-verifier`. In 0.6.1 and later, each synced skill also gets a generated `ZEN_CAD_WORKSPACE.md` file that records the Zen CAD repository root.

Important: CoBrA skill sync installs the workflow skills and workspace binding only. It does not change the CoBrA process working directory. Start the CoBrA daemon or session from the Zen CAD repository root when possible; otherwise the installed `/agentic-cad` skill should read its sibling `ZEN_CAD_WORKSPACE.md` and use that path. For the adapter contract, also see `docs/harness_adapters.md` and `plugins/cobra/README.md`.

Use `doctor` whenever the first-run state is unclear:

```bash
./zen-cad doctor
```

## Prompt-first milestone startup

After setup, the user does not need to run another Python command to create a CAD job. In a new CoBrA session or prompt window, the user can simply type a natural-language CAD goal such as:

```text
기어 박스를 만들고 싶어
```

The agent should treat that prompt as the milestone creation request. Do not ask the user to run a Python command, and do not require the user to manually choose a milestone id/title. Internally run this command from the Zen CAD repository root:

```bash
python3 scripts/new_milestone.py --request "<goal>"
```

The repo-local wrapper is equivalent for manual use:

```bash
./zen-cad new "<goal>"
```

Use the wrapper only when you intentionally want to create a milestone from the terminal instead of through a CoBrA prompt.

For example, `기어 박스를 만들고 싶어` should create the next available milestone such as `003_gearbox` with title `Gearbox` in this repository because `002_nema17_mount_plate` is the bundled final demo. Then follow `prompts/new_milestone.md`, generate a first concept/layout CAD artifact with CoBrA's available tools, keep unresolved standard parts as explicit proxies/blockers, and run `./zen-cad validate --level structure milestones/<id>` before reporting the first artifact paths.

CoBrA is the harness layer: use it for CAD generation, file edits, terminal execution, web/catalog lookup, memory, and worker delegation. Zen CAD is the lightweight workflow/evidence layer: use its strict CLI gates only when deciding whether a CAD result is final/release-grade.

If `./zen-cad doctor` reports missing CoBrA skills or missing workspace binding, rerun `./zen-cad init --with-cobra`. If it reports `ENV_BLOCKED` for `numpy`, `trimesh`, `build123d`, or OCP, that is a final CAD evidence environment issue, not a CoBrA skill discovery issue.

The setup helper still supports `--milestone-request` for automation or smoke tests, and explicit `--milestone-id` plus `--milestone-title` still works when an exact folder name must be pinned.
