# Zen CAD Project Kickoff Prompt

Use `/agentic-cad` as the top-level workflow. Treat this repository as a portable Zen CAD operating environment that leverages the host harness for actual CAD generation. Create CAD jobs as milestones, generate a concept/layout artifact early, and require validation-script evidence only before final/release completion claims.

## Prompt-first milestone startup

If the user starts a new CoBrA/agent session by stating a CAD goal such as `기어 박스를 만들고 싶어`, treat that as a milestone-start request. Do not ask the user to run a Python command or manually choose a milestone id/title. Internally run `python3 scripts/new_milestone.py --request "<goal>"` from the Zen CAD repository root, confirm the created milestone such as `003_gearbox` titled `Gearbox` in this repository, then continue with the new milestone artifacts.

Zen CAD is harness-native and generation-first. Start new work at `maturity: concept`, generate useful custom/envelope CAD with the available harness toolchain, and reserve final completion claims for `maturity: final` evidence.

First response requirements:

- confirm the active milestone id/title and assumptions;
- identify standard/off-the-shelf parts that may remain proxy/source-lock blockers during concept/layout work;
- identify likely custom CAD parts;
- name required artifacts and validation evidence;
- do not generate standard parts as final geometry without sourcing evidence.
