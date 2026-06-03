# Claude Code-Style Adapter

Use Zen CAD as repository-local skills plus an optional validation CLI.

1. Open the Zen CAD repository in Claude Code or a similar coding harness.
2. Ask the agent to follow `skills/agentic-cad/SKILL.md` for the CAD workflow.
3. Keep each CAD job in `milestones/<id>/`.
4. Use the harness for CAD generation, web/catalog lookup, file edits, CAD script execution, and review loops.
5. Run `./zen-cad validate --level structure milestones/<id>` after milestone/artifact creation.

First deliverable target: a real concept/layout CAD source/export created by the available harness toolchain.

Final CAD completion still requires CLI evidence from the shipped milestone path, not a screenshot or verbal report:

```bash
./zen-cad doctor --cad-required
./zen-cad validate --level completion milestones/<id>
```
