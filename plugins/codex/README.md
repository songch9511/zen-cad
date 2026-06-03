# Codex-Style Adapter

Use Zen CAD as a Codex-style skill/plugin workspace rather than as a standalone CAD app.

1. Open the Zen CAD repository as the working directory.
2. Load `skills/agentic-cad/SKILL.md` as the top-level CAD workflow instruction.
3. For custom CAD implementation handoffs, load `skills/spec-to-cad/SKILL.md`.
4. Let Codex use its normal file editing, terminal execution, and available CAD/generation tools.
5. Deliver a concept/layout CAD artifact first; reserve strict Zen CAD gates for final claims.

If the earthtojake/text-to-cad CAD skill or plugin is installed in the Codex environment, use it as the preferred STEP-first CAD execution path. Zen CAD supplies the milestone and evidence harness around that CAD execution. For final claims, record command-backed `cad_generation`, `step_load`, and `geometry_inspection` checks with artifact sizes and SHA-256 hashes in the active milestone.

Suggested first prompt:

```text
Use skills/agentic-cad/SKILL.md in this repository. Create a prompt-first Zen CAD milestone for: <goal>. Generate the first CAD artifact with the available Codex/CAD toolchain. Mark unresolved sourcing/env issues as concept/layout blockers, not as a reason to stop before CAD exists. Before any final claim, write command-backed validation evidence with artifact hashes and run ./zen-cad validate --level completion milestones/<id>.
```

If the Codex environment supports plugin manifests, package `skills/`, `docs/harness_adapters.md`, and the `./zen-cad` wrapper as the installable payload. The validation CLI should remain callable from the checked-out repository root for structure checks and optional final/release gates.
