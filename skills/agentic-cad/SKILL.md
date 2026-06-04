---
name: agentic-cad
description: Deprecated Zen CAD compatibility entrypoint. Route new mechanical CAD work to cad-spec, assembly-layout, interface-signatures, and cad-handoff; use this only when older prompts explicitly invoke agentic-cad.
version: 0.8.0
---

# Agentic CAD Compatibility Shim

`agentic-cad` is deprecated in Zen CAD 0.8.0. It used to be a broad orchestrator that mixed requirements, sourcing, CAD generation, validation, BOM, and reporting. New work should use focused skills instead.

## Route New Work

- Use `/cad-spec` first for natural-language mechanical requests, assembly-first specs, coordinate frames, interface primitives, locked layout facts, proxy fidelity policy, proceed gates, and downstream CAD handoffs.
- Use `/assembly-layout` when the task is specifically about assembly graph, contacts, connections, motion relationships, layout review, or locked-fact drift.
- Use `/interface-signatures` when standard component interface facts are needed before source-locked STEP geometry exists.
- Use `/cad-handoff` when an approved spec needs to be handed to the active CAD harness, `$cad`, text-to-cad, build123d, CadQuery, FreeCAD, or another generator.

Legacy 0.7 skills such as `/source-step-parts`, `/spec-to-cad`, `/mechanism-kinematics`, `/cad-artifact-reviewer`, `/manufacturing-preflight`, and `/self-evolving-producer-verifier` remain available for existing milestone/evidence workflows, but they are no longer the default starting point.

## Compatibility Behavior

If a user explicitly invokes `/agentic-cad`, do not run the old all-in-one workflow. Start by writing a CAD-native spec:

```text
Use /cad-spec to turn this request into a CAD-native layout spec.
Then use /cad-handoff to brief the active CAD-generation harness.
```

Only use legacy milestone commands such as `./zen-cad new`, `./zen-cad validate`, or `./zen-cad source-lock` when the user is working inside an existing Zen CAD milestone or explicitly asks for legacy final-evidence packaging.

## Boundary

This shim must stay small. Do not add milestone schemas, validation gates, part registry policy, sourcing rules, or CAD generation procedures here. Put those responsibilities in focused skills or references.
