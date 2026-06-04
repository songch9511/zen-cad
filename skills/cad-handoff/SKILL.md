---
name: cad-handoff
description: Convert a CAD-native spec into a concise downstream brief for a CAD-generation harness. Use for Codex, CoBrA, text-to-cad/$cad, build123d, CadQuery, FreeCAD, or other generators, especially when preserving layout locked facts through detail modeling.
version: 0.8.0
---

# CAD Handoff

## Purpose

Use this skill after `cad-spec` has produced a CAD-native spec and the next step is to ask a CAD-generation harness to create or update geometry.

This skill is adapter-specific. Keep Codex, CoBrA, `$cad`, file paths, tool launchers, and environment details here instead of in the core `cad-spec` skill.

## Use This Skill When

Use it when:

- the user wants to proceed from spec to CAD;
- a layout proxy should be generated from locked facts;
- a detail model should preserve an approved layout;
- the target harness is Codex, CoBrA, text-to-cad, build123d, CadQuery, FreeCAD, or unknown.

## Workflow

1. Read the CAD spec and identify target maturity: layout, detail, or final.
2. Identify the downstream harness/toolchain.
3. Preserve locked facts verbatim in the handoff.
4. State proxy simplifications allowed for layout.
5. State checks or review links expected from the generator.
6. State when the generator must stop and return to layout review.

## Handoff Skeleton

```text
Task: Generate <layout proxy | detail CAD> from the attached CAD spec.
Primary goal:
Locked facts:
Allowed simplifications:
Required outputs:
Required checks:
Stop conditions:
Known assumptions:
```

## Non-Negotiables

- Do not hide locked facts in a summary; include them explicitly.
- Do not ask for high-fidelity geometry during layout unless the user requested it.
- Do not let the downstream generator change approved layout facts during detail.
- Do not claim final evidence unless the downstream tool actually produced it.

## References

- `references/harness-briefs.md` — Codex, CoBrA, `$cad`, and generic handoff templates.
