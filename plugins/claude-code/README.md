# Claude Code-Style Adapter

Use Zen CAD as repository-local spec skills plus an optional legacy CLI.

1. Open the Zen CAD repository in Claude Code or a similar coding harness.
2. Start with `skills/cad-spec/SKILL.md`.
3. Use `skills/assembly-layout/SKILL.md`, `skills/interface-signatures/SKILL.md`, and `skills/cad-handoff/SKILL.md` only when their focused scope applies.
4. Let the harness or installed CAD tools generate geometry from the resulting spec.

First deliverable target: a CAD-native layout spec with a proceed gate. The first CAD artifact, if generated, should be a low-detail layout proxy whose assembly positioning and interfaces are correct.

Legacy final-evidence validation is still available through:

```bash
./zen-cad validate --level completion milestones/<id>
```
