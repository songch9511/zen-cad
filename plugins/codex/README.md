# Codex-Style Adapter

Use Zen CAD as a spec-first skill workspace.

1. Open this repository as the working directory.
2. Start new work with `skills/cad-spec/SKILL.md`.
3. Use `skills/assembly-layout/SKILL.md` for layout/proceed review.
4. Use `skills/interface-signatures/SKILL.md` for layout-ready standard interface facts.
5. Use `skills/cad-handoff/SKILL.md` to brief Codex, `$cad`, text-to-cad, build123d, or another CAD generator.

Suggested first prompt:

```text
Use skills/cad-spec/SKILL.md to write a CAD-native layout spec for: <goal>.
Focus on coordinate frames, interface primitives, motion/drivetrain relationships, locked layout facts, proxy fidelity, and the proceed gate. Do not generate final CAD yet.
```

Legacy `./zen-cad` milestone commands remain available only for older evidence-harness workflows.
