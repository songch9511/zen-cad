---
name: cad-spec
description: Write CAD-native mechanical specs from natural-language design requests before CAD generation. Use for assembly-first layout specs, interface definitions, coordinate frames, datums, motion/drivetrain relationships, proxy fidelity boundaries, proceed gates, and downstream handoffs to CAD-generation harnesses such as Codex, text-to-cad, build123d, or FreeCAD.
version: 0.8.0
---

# CAD Spec

## Purpose

Use this skill before asking a CAD-generation agent or CAD toolchain to create geometry. It converts a user's natural-language mechanical request into a CAD-native spec that a downstream harness can model, inspect, and revise.

This skill does not generate CAD, source STEP parts, run validation gates, create BOMs, or package final reports. Its job is to make the first modeling brief precise enough that the generated assembly has correct positioning, interfaces, and motion relationships even when the visual detail is intentionally low.

Core rule: **spec the assembly contract before generating CAD.** For assemblies, prioritize coordinate frames, datums, axes, mating primitives, center distances, clearances, transmission relationships, and locked layout facts over surface fidelity.

## Use This Skill When

Use `cad-spec` when the user asks for:

- a mechanical part or assembly from prose;
- an assembly with motors, bearings, belts, pulleys, gears, rails, shafts, fasteners, or moving interfaces;
- a first-pass layout proxy whose coupling structure must be correct;
- a proceed/review checkpoint before detail modeling;
- a downstream handoff to the active CAD harness, `$cad`, text-to-cad, build123d, CadQuery, FreeCAD, or another CAD generator.

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

Ask one focused question only when missing information makes the layout impossible, fit-critical, safety-critical, or compliance-bound. Otherwise proceed with named assumptions and mark them as not locked.

## Required Workflow

1. Classify the request as single part, static assembly, moving assembly, modification, inspection brief, or downstream handoff.
2. Load only the relevant references listed below.
3. Write a concise CAD-native Markdown spec. Do not ask the user to provide JSON/YAML.
4. Define the coordinate system, root frame, part-local frames, and dominant datums.
5. Define the assembly graph: parts, roles, fixed/moving relationships, and repeated component families.
6. Define interface primitives: planes, cylinders, bores, shafts, bolt circles, pitch circles, rails, slots, belt planes, gear mesh references, cable/keep-out envelopes, and fastener axes.
7. Define motion or drivetrain relationships when present.
8. Define proxy fidelity boundaries: what may be simplified and what must remain dimensionally meaningful.
9. Define locked layout facts and a proceed gate so the user can approve positioning before detail modeling.
10. Write a downstream CAD handoff targeted to the active harness.

## Required Spec Sections

Every useful spec should include:

```text
# CAD Spec: <short name>

## Intent
## Coordinate System
## Parts And Roles
## Assembly Graph
## Interface Primitives
## Motion And Drivetrain
## Proxy Fidelity Policy
## Locked Layout Facts
## Assumptions And Open Questions
## Proceed Gate
## Downstream CAD Handoff
```

Omit a section only when it is truly out of scope, and say why.

## Non-Negotiables

- Do not bury positioning facts inside prose-only descriptions. Name the datum, axis, frame, or interface primitive.
- Do not let surface detail outrank assembly correctness in the first pass.
- Do not source-lock or crawl for catalog parts before writing the layout spec.
- Do not claim a proxy is final geometry.
- Do not allow detail modeling to change locked layout facts without returning to the proceed gate.
- Do not present CAD validation, viewer screenshots, or generated geometry as engineering certification.
- Do not embed Zen CAD repository paths, milestone folders, or harness workspace paths in the core spec unless the downstream handoff specifically requires them.

## Progressive References

Load these files only when the trigger applies:

- `references/natural-language-to-cad-spec.md` — converting prose requests into a CAD-native spec.
- `references/assembly-positioning.md` — root frames, part-local datums, mating primitives, center distances, and locked facts.
- `references/interface-primitives.md` — planes, cylinders, bores, shafts, bolt patterns, pitch references, rails, slots, and fastener axes.
- `references/motion-and-drivetrain.md` — belts, pulleys, gears, screws, sliders, rotary axes, limits, and transmission relationships.
- `references/proxy-fidelity.md` — what layout proxies may simplify and what they must preserve.
- `references/proceed-gate.md` — user approval, locked facts, and detail-stage drift rules.
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
