# CoBrA Usage

From the Zen CAD repository root, run setup once:

```bash
./zen-cad init --with-cobra
```

That command syncs the bundled `/agentic-cad`, `/spec-to-cad`, and `/self-evolving-producer-verifier` skills into the CoBrA skills directory and runs the bundled validation checks.

Important: CoBrA skill sync installs the workflow skills only. It does not register this repository as the active CoBrA workspace. Start the CoBrA daemon or session from the Zen CAD repository root, or explicitly point the agent to this repository path in the prompt.

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

For example, `기어 박스를 만들고 싶어` should create the next available milestone such as `003_gearbox` with title `Gearbox` in this repository because `002_nema17_mount_plate` is the bundled final demo. Then follow `prompts/new_milestone.md`, keep standard parts source-first for final evidence, allow concept/layout proxy CAD when explicitly marked non-final, and require `./zen-cad validate-completion milestones/<id>` evidence before reporting final completion.

The setup helper still supports `--milestone-request` for automation or smoke tests, and explicit `--milestone-id` plus `--milestone-title` still works when an exact folder name must be pinned.
