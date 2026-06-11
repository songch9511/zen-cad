---
name: constrained-detail-cad
description: Generate custom/detail CAD from locked layout facts and user shape intent while preserving protected interface frames, clearances, mounting datums, bores, shafts, bolt patterns, pitch references, and motion envelopes. Use for custom brackets, plates, covers, housings, adapters, and generated detail_shape_plan artifacts.
---

# Constrained Detail CAD

Use this skill when a custom part needs a user-desired shape, but the layout proxy has already established facts that cannot move. Standard/catalog parts should usually use `cad-replacement`; custom parts should use this constrained generation workflow. In this workflow, locked facts are hard constraints and style is negotiable.

## Required Workflow

1. Read the CAD spec, layout proxy scene, locked facts, interface frames, and user shape request.
2. Load `references/detail-shape-plan.md`.
3. Separate the part into protected interface zones, functional structure zones, and freeform/style zones.
4. Convert the user's desired appearance into `shape_intent`: style, manufacturing method, minimum wall, preferred fillets/chamfers, and avoid list.
5. Write or update a `detail_shape_plan` artifact before generating CAD.
6. Generate geometry by placing protected interface features first, then structural features, then style/freeform features.
7. Export a detail candidate and inspect it against locked facts. The user's requested shape is allowed only inside the feasible space left by protected zones and clearance rules.
8. Repair source-level causes when checks fail. Do not tune visually or move locked interfaces to make the shape look better.

## Hard Rules

- Locked facts are hard constraints; shape intent is a soft constraint.
- Protected zones cannot be cut, moved, resized, or obscured by style features.
- A generated detail part cannot proceed until bores, shafts, bolt patterns, mounting planes, clearances, and relevant motion envelopes are measured after export.
- If the requested shape conflicts with a locked fact, report the conflict and propose a shape adjustment instead of changing the locked fact.

## Outputs

- `detail_shape_plan` for every generated custom part.
- Generated CAD source and STEP/STP detail candidate when the active CAD harness supports generation.
- Inspection report with locked fact measurements and skipped checks.

## References

- `references/detail-shape-plan.md` — detail shape plan structure, zone model, feature ordering, and inspection gates.
