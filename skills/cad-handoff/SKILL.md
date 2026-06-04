---
name: cad-handoff
description: Convert a CAD-native spec into a concise downstream brief for a CAD-generation harness. Use for Codex, text-to-cad/$cad, build123d, CadQuery, FreeCAD, or other generators, especially when preserving layout locked facts, parameter contracts, inspection plans, and repair loops through CAD generation and detail modeling.
version: 0.8.0
---

# CAD Handoff

## Purpose

Use this skill after `cad-spec` has produced a CAD-native spec and the next step is to ask a CAD-generation harness to create, inspect, repair, or update geometry.

This skill is adapter-specific. Keep harness names, `$cad`, file paths, tool launchers, and environment details here instead of in the core `cad-spec` skill.

## Use This Skill When

Use it when:

- the user wants to proceed from spec to CAD;
- a layout proxy should be generated from locked facts;
- a detail model should preserve an approved layout;
- downstream generation needs explicit source, STEP/STP, snapshot, viewer, or secondary export targets;
- inspection or repair expectations must be carried into the generator prompt;
- the target harness is Codex, text-to-cad, build123d, CadQuery, FreeCAD, or unknown.

## Workflow

1. Read the CAD spec and identify target maturity: layout, detail, or final.
2. Identify the downstream harness/toolchain.
3. Preserve locked facts verbatim in the handoff.
4. Preserve the parameter contract and mark locked, assumed, and derived values.
5. State source intent, primary artifact, secondary outputs, and review artifacts.
6. State proxy simplifications allowed for layout.
7. State deterministic checks, snapshot/viewer expectations, and skipped-check reporting.
8. State source-of-truth, generated files, repair attempts, and claims that must not be made.
9. State the repair loop and when the generator must stop and return to layout review.

## Handoff Skeleton

```text
Task: Generate <layout proxy | detail CAD> from the attached CAD spec.
Primary goal:
Source-of-truth:
Generated files:
Locked facts:
Parameter contract:
Artifact targets:
Allowed simplifications:
Required outputs:
Required checks:
Validation actually run:
Skipped checks and reasons:
Snapshot/viewer evidence:
Repair loop:
Repair attempts:
Stop conditions:
Known assumptions:
Claims not made:
```

## Non-Negotiables

- Do not hide locked facts in a summary; include them explicitly.
- Do not drop the parameter contract when moving from spec to generator prompt.
- Do not ask for high-fidelity geometry during layout unless the user requested it.
- Do not treat a screenshot or viewer link as a substitute for geometry checks.
- Do not validate generated CAD by git diff, file size, or generated-file churn.
- Do not let the downstream generator change approved layout facts during detail.
- Do not claim final readiness unless the downstream tool actually produced the required outputs.

## References

- `references/harness-briefs.md` — Codex, `$cad`, and generic handoff templates.
- `references/runtime-contract.md` — keeping core specs kernel-neutral while adapter prompts map to active runtime tools.
