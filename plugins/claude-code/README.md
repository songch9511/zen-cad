# Claude Code-Style Adapter

Use Zen CAD as repository-local skills plus an optional validation CLI.

1. Open the Zen CAD repository in Claude Code or a similar coding harness.
2. Ask the agent to follow `skills/agentic-cad/SKILL.md` for the CAD workflow.
3. Keep each CAD job in `milestones/<id>/`.
4. Use the harness for CAD generation, web/catalog lookup, file edits, CAD script execution, and review loops.
5. Run `./zen-cad validate --level structure milestones/<id>` after milestone/artifact creation.

First deliverable target: a real concept/layout CAD source/export created by the available harness toolchain.

If earthtojake/text-to-cad is available to Claude Code, use that CAD skill for STEP-first generation, deterministic inspection, and snapshot review. Otherwise use a project-approved build123d, CadQuery, FreeCAD, OpenSCAD, or equivalent kernel-backed path. Final evidence must record command-backed `cad_generation`, `step_load`, and `geometry_inspection` checks with matching artifact sizes and SHA-256 hashes.

Final CAD completion still requires CLI evidence from the shipped milestone path, not a screenshot or verbal report:

```bash
./zen-cad doctor --cad-required
./zen-cad validate --level completion milestones/<id>
```
