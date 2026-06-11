---
name: cad-handoff
description: Convert a CAD-native spec into a concise downstream brief for a CAD-generation harness. Use for Codex, text-to-cad/$cad, build123d, CadQuery, FreeCAD, or other generators, especially when preserving layout locked facts, parameter contracts, feature plans, inspection plans, and repair loops through CAD generation and detail modeling.
version: 1.0.2
---

# CAD Handoff

## Purpose

Use this skill after `cad-spec` has produced a CAD-native spec and the next step is to create, inspect, repair, or update geometry. For `build123d` targets, Zen CAD can execute generated source into a first-pass STEP artifact. For approved detail handoffs targeted at CAD Skills/text-to-cad, this skill can also package a downstream prompt bundle.

This skill is adapter-specific. Keep harness names, `$cad`, file paths, tool launchers, and environment details here instead of in the core `cad-spec` skill.

## Use This Skill When

Use it when:

- the user wants to proceed from spec to CAD;
- a layout proxy should be generated from locked facts;
- a generated build123d source file should be executed into a primary STEP artifact;
- a detail model should preserve an approved layout;
- downstream generation needs explicit source, STEP/STP, snapshot, viewer, or secondary export targets;
- inspection or repair expectations must be carried into the generator prompt;
- visual inspection and engineering-rule repair expectations must be preserved through generation;
- the target harness is Codex, text-to-cad, build123d, CadQuery, FreeCAD, or unknown;
- generated STEP artifacts should be paired with local viewer links for proceed review.

## Workflow

1. Read the CAD spec and identify target maturity: layout, detail, or final.
2. Identify the downstream harness/toolchain.
3. State the Subagent Dispatch Plan for generation/review/repair, including explicit sequential fallback if subagents are unavailable.
4. Preserve locked facts verbatim in the handoff.
5. Preserve the parameter contract and mark locked, assumed, and derived values.
6. State source intent, primary artifact, secondary outputs, and review artifacts.
7. State proxy simplifications allowed for layout.
8. State deterministic checks, snapshot/viewer expectations, and skipped-check reporting.
9. State visual inspection requirements for fastening, clearance, floating body, interference, mesh/alignment, and engineering plausibility issues.
10. State source-of-truth, generated files, repair attempts, and claims that must not be made.
11. State the repair loop and when the generator must stop and return to layout review.
12. For `build123d` targets, run `tools/generate_cad_artifact.py` or the runner's build123d generation step before proceed review.
13. For generated STEP artifacts, include `tools/package_viewer_link.py` output or the runner's `viewer_link.html` in proceed review when a local viewer is available.
14. For an approved `text-to-cad` handoff packet, package the prompt bundle with `tools/package_text_to_cad_bundle.py`.

## Handoff Skeleton

```text
Task: Generate <layout proxy | detail CAD> from the attached CAD spec.
Primary goal:
Source-of-truth:
Generated files:
Locked facts:
Subagent dispatch plan:
Parameter contract:
Artifact targets:
Feature plan:
Allowed simplifications:
Required outputs:
Required checks:
Visual/engineering review:
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
- Do not drop the Subagent Dispatch Plan when moving from spec to generator prompt; if subagents are unavailable, state the sequential fallback explicitly.
- Do not ask for high-fidelity geometry during layout unless the user requested it.
- Do not treat a screenshot or viewer link as a substitute for geometry checks.
- Do not close a generated assembly review while visible fastening, clearance, floating body, interference, or mesh/alignment concerns remain unclassified.
- Do not validate generated CAD by git diff, file size, or generated-file churn.
- Do not let the downstream generator change approved layout facts during detail.
- Do not claim final readiness unless the downstream tool actually produced the required outputs.
- Do not treat Zen CAD's first-pass STEP export as supplier-verified or manufacturing-ready geometry.
- Do not generate CAD, STEP/STP, snapshots, or viewer links while packaging a text-to-cad prompt bundle.

## References

- `references/harness-briefs.md` — Codex, `$cad`, and generic handoff templates.
- `references/runtime-contract.md` — keeping core specs kernel-neutral while adapter prompts map to active runtime tools.
- `references/text-to-cad-adapter-contract.md` — approved handoff to CAD Skills/text-to-cad prompt bundle contract.
