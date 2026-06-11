---
name: cad-spec
description: Write CAD-native mechanical specs from natural-language design requests and orchestrate CAD work through specialist subagents when available. Use for assembly-first layout specs, parameter contracts, artifact targets, inspection plans, interface definitions, coordinate frames, datums, motion/drivetrain relationships, visual inspection and repair loops, proxy fidelity boundaries, proceed gates, subagent delegation, and downstream CAD handoffs.
version: 1.0.2
---

# CAD Spec

## Purpose

Use this skill before asking a CAD-generation agent or CAD toolchain to create geometry. It converts a user's natural-language mechanical request into a CAD-native spec that a downstream harness can model, inspect, repair, and revise.

This skill owns the spec and assembly contract. It also defines the parameter contract, artifact targets, inspection plan, repair rules, and downstream handoff. It may coordinate CAD work by delegating bounded specialist subtasks when the harness supports subagents. It should not perform catalog crawling, manufacturing certification, or broad report packaging.

Core rule: **spec the assembly contract before generating CAD.** For assemblies, prioritize coordinate frames, datums, axes, mating primitives, center distances, clearances, transmission relationships, and locked layout facts over surface fidelity.

## Use This Skill When

Use `cad-spec` when the user asks for:

- a mechanical part or assembly from prose;
- an assembly with motors, bearings, belts, pulleys, gears, rails, shafts, fasteners, or moving interfaces;
- a first-pass layout proxy whose coupling structure must be correct;
- a proceed/review checkpoint before detail modeling;
- a parameterized CAD brief with named dimensions, derived relationships, and validation targets;
- artifact targets for source, STEP/STP, snapshots, viewer links, or secondary exports;
- specialist subagents for layout, interfaces, motion, CAD generation, visual inspection, engineering review, or repair;
- local build123d STEP generation or a downstream handoff to `$cad`, text-to-cad, CadQuery, FreeCAD, or another CAD generator.
- native feature-aware generation for holes, bores, bolt-circle patterns, repeated hole patterns, rectangular top chamfers, simplified gear teeth, or supported cylinder edge-round approximations.

Do not use this skill for CAM, G-code, visual concept art, FEA, procurement-ready sourcing, or manufacturing certification unless the user first needs a CAD-native spec for those downstream tasks.

## Default Assumptions

Use these defaults unless the user specifies otherwise:

- Units: millimeters.
- Angles: degrees in prose, radians only when a downstream API requires them.
- Root frame: stable mounting/base component when known; otherwise the assembly footprint center.
- Base plane: XY.
- Up axis: +Z.
- First artifact target: low-detail `layout_proxy`.
- Surface fidelity: intentionally low for layout; boxes, cylinders, envelopes, simplified teeth, and coarse sweeps are acceptable.
- Interface fidelity: high from the first pass; axes, bores, mounting faces, bolt patterns, pitch references, and clearances must be explicit.
- Primary artifact intent: STEP/STP when the active CAD generator supports it.
- Parameter policy: named parameters with units, source, locked status, driven features, and validation targets.

Ask one focused question only when missing information makes the layout impossible, fit-critical, safety-critical, or compliance-bound. Otherwise proceed with named assumptions and mark them as not locked.

## Required Workflow

1. Classify the request as single part, static assembly, moving assembly, modification, inspection brief, or downstream handoff.
2. Load only the relevant references listed below.
3. Write a concise CAD-native Markdown spec. Do not ask the user to provide JSON/YAML.
4. Define the coordinate system, root frame, part-local frames, and dominant datums.
5. Define named parameters, units, selected values, locked/assumed/derived status, driven features, and validation targets.
6. Define artifact targets: maturity, CAD source intent, primary CAD artifact, secondary outputs, and review evidence.
7. Define the assembly graph: parts, roles, fixed/moving relationships, and repeated component families.
8. Define interface primitives: planes, cylinders, bores, shafts, bolt circles, pitch circles, rails, slots, belt planes, gear mesh references, cable/keep-out envelopes, and fastener axes.
9. Define motion or drivetrain relationships when present.
10. Define proxy fidelity boundaries: what may be simplified and what must remain dimensionally meaningful.
11. Define locked layout facts and a proceed gate so the user can approve positioning before detail modeling.
12. Define an inspection plan and repair loop for generated CAD.
13. If CAD generation or review is requested, write a Subagent Dispatch Plan before generating geometry, then spawn specialist subagents where the harness supports delegation.
14. Define a visual inspection and engineering repair plan for generated CAD: required views, issue taxonomy, measurable checks, and repair stop conditions.
15. If the active target is build123d and generation is requested, run the build123d source/export/inspection path before proceed review.
16. If a viewer is available, capture review evidence and inspect it for fastening, clearance, floating body, interference, mesh/alignment, and engineering plausibility issues.
17. If native build123d generation needs detail features, encode them in `cad_spec.extensions.cad_feature_plan` instead of burying them in prose.
18. Write a downstream CAD handoff targeted to the active harness when external generation or detail upgrade is needed.

## Machine-Readable Contracts

Do not ask users to write JSON or YAML. When a harness needs machine-readable artifacts, derive them from the Markdown spec using the repo-level schemas:

- `schemas/cad_spec.schema.json`
- `schemas/layout_contract.schema.json`
- `schemas/interface_signature.schema.json`
- `schemas/inspection_report.schema.json`
- `schemas/handoff_packet.schema.json`
- `schemas/layout_proxy_scene.schema.json`
- `schemas/cad_source_manifest.schema.json`
- `schemas/proceed_gate_package.schema.json`
- `schemas/proceed_approval.schema.json`
- `schemas/pipeline_run.schema.json`
- `schemas/source_lock_evidence.schema.json`

Use `source_lock_evidence` only for final-stage standard/catalog part sourcing. It records explicit step.parts, manufacturer, datasheet, project-file, or user-provided evidence without treating layout interface signatures as final proof.

Use `registry/interfaces/index.json` for built-in layout-ready interface signatures before attempting external catalog research.

## Specialist Subagents

Use subagents for complex assemblies, moving mechanisms, generated CAD review, visual inspection, engineering plausibility checks, or any task where independent layout/interface/motion/review work can run in parallel. Keep the lead agent responsible for the final spec and for reconciling conflicts.

When the user asks for CAD generation, generated artifact review, or repair, the lead must create a **Subagent Dispatch Plan** before generating or revising geometry. The plan must name each bounded role, input artifacts, expected output, and stop condition. If the active harness exposes subagents, spawn the listed roles. If subagents are unavailable, explicitly state `Subagent status: unavailable; using sequential fallback roles` and run the same roles sequentially before finalizing.

Default specialist roles:

- `layout-specialist`: root frame, part-local frames, assembly graph, contacts, connections, locked layout facts.
- `interface-specialist`: standard component interface signatures, bolt patterns, bores, shafts, rails, belts, envelopes, and must-confirm facts.
- `parameter-specialist`: named parameters, defaults, derived values, allowed ranges, driven features, and validation targets.
- `motion-specialist`: joints, travel, transmission ratios, gear/belt/screw relationships, motion limits, and keep-outs.
- `cad-generator`: low-detail layout proxy or detail CAD from the approved spec, preserving locked facts.
- `cad-reviewer`: compare generated CAD against parameters, locked facts, inspection plan, proceed gate, allowed simplifications, and stated assumptions.
- `visual-reviewer`: inspect viewer snapshots/multi-view evidence for floating bodies, unintended intersections, missing fasteners, insufficient clearances, misaligned axes/planes, and visibly implausible load paths.
- `engineering-reviewer`: convert visual concerns into measurable checks for fastening engagement, shaft/bore fit, bearing support, belt or gear mesh, wall thickness, support, clearance, and assembly feasibility.

Spawn only bounded tasks. Give each subagent the minimum relevant spec sections, expected output, and stop conditions. Do not ask subagents to browse broadly for parts, invent final ratings, or rewrite the whole spec. If subagents are unavailable, perform the same roles as sequential local passes.

## Required Spec Sections

Every useful spec should include:

```text
# CAD Spec: <short name>

## Intent
## Coordinate System
## Parameter Contract
## Artifact Targets
## Parts And Roles
## Assembly Graph
## Interface Primitives
## Motion And Drivetrain
## Proxy Fidelity Policy
## Locked Layout Facts
## Inspection Plan
## Repair Loop
## Visual Inspection And Engineering Review
## Assumptions And Open Questions
## Proceed Gate
## Downstream CAD Handoff
```

Omit a section only when it is truly out of scope, and say why.

## Non-Negotiables

- Do not bury positioning facts inside prose-only descriptions. Name the datum, axis, frame, or interface primitive.
- Do not let surface detail outrank assembly correctness in the first pass.
- Do not crawl catalogs before writing the layout spec.
- Do not crawl catalogs before checking the built-in interface registry for layout-ready facts.
- Do not claim a proxy is final geometry.
- Do not hand off CAD generation without named parameters and validation targets for critical dimensions.
- Do not treat screenshots or viewer links as substitutes for geometry facts, measurements, frames, or mate checks.
- Do not close proceed review on generated assemblies until floating bodies, unintended interference, fastening/clearance concerns, and visible mesh/alignment concerns are either checked, repaired, or recorded as skipped with a concrete reason.
- Do not allow detail modeling to change locked layout facts without returning to the proceed gate.
- Do not present CAD validation, viewer screenshots, or generated geometry as engineering certification.
- Do not claim selector-based topology fillets/chamfers unless the active build123d/OCP runtime actually ran those operations; use the inspection report limitations when approximations are used.
- Do not embed repository paths or harness workspace paths in the core spec unless the downstream handoff specifically requires them.

## Progressive References

Load these files only when the trigger applies:

- `references/natural-language-to-cad-spec.md` — converting prose requests into a CAD-native spec.
- `references/parameter-contract.md` — named parameters, units, locked/assumed/derived status, and validation targets.
- `references/export-targets.md` — layout/detail/final maturity, source intent, primary artifacts, secondary exports, and review evidence.
- `references/assembly-positioning.md` — root frames, part-local datums, mating primitives, center distances, and locked facts.
- `references/interface-primitives.md` — planes, cylinders, bores, shafts, bolt patterns, pitch references, rails, slots, and fastener axes.
- `references/motion-and-drivetrain.md` — belts, pulleys, gears, screws, sliders, rotary axes, limits, and transmission relationships.
- `references/proxy-fidelity.md` — what layout proxies may simplify and what they must preserve.
- `references/inspection-and-repair.md` — generated CAD checks, snapshot/viewer expectations, failure classes, and repair loops.
- `references/visual-inspection-and-repair.md` — multi-view visual review, issue taxonomy, engineering plausibility checks, and visual-to-measurable repair loops.
- `references/proceed-gate.md` — user approval, locked facts, and detail-stage drift rules.
- `references/specialist-subagents.md` — when and how to delegate CAD work to specialist subagents.
- `references/downstream-cad-handoff.md` — active harness, `$cad`, text-to-cad, and generic CAD generator handoffs.

## Final Response

Return the spec itself or the path where you wrote it, plus a short handoff summary:

```text
Spec status: ready for layout CAD | needs one clarification | blocked
Layout risk: <main positioning or interface risk>
Proceed gate: <what the user must approve before detail modeling>
Downstream target: <harness/toolchain if known>
```

If the user asked you to continue into CAD generation and the appropriate CAD skill/tool is available, hand off the spec after writing it. Otherwise stop at the spec and state the next command or skill target plainly.
