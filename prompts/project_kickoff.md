# Zen CAD Project Kickoff Prompt

Use `/agentic-cad` as the top-level workflow. Treat this repository as a portable Zen CAD operating environment, not a one-off text-to-CAD task. Preserve the source-first/generate-second rule, create CAD jobs as milestones, and require validation-script evidence before completion claims.

## Prompt-first milestone startup

If the user starts a new CoBrA/agent session by stating a CAD goal such as `기어 박스를 만들고 싶어`, treat that as a milestone-start request. Do not ask the user to run a Python command or manually choose a milestone id/title. Internally run `python3 scripts/new_milestone.py --request "<goal>"` from the Zen CAD repository root, confirm the created milestone such as `003_gearbox` titled `Gearbox` in this repository, then continue with the new milestone artifacts.

0.5.0 is generation-first. Start new work at `maturity: concept`, generate useful custom/envelope CAD when possible, and reserve final completion claims for `maturity: final` evidence.

First response requirements:

- confirm the active milestone id/title and assumptions;
- identify standard/off-the-shelf parts to source first;
- identify likely custom CAD parts;
- name required artifacts and validation evidence;
- do not generate standard parts as final geometry without sourcing evidence.
