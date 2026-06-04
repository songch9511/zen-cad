---
name: mechanism-kinematics
description: Build and review Zen CAD mechanism kinematic contracts from assemblies, frames, joints, axes, travel limits, CONTACT_MAP, CONNECTIONS, and optional URDF/SDF/SRDF handoff data.
version: 0.8.0
---

# Mechanism Kinematics

## Purpose

`/mechanism-kinematics` captures the motion contract for Zen CAD assemblies. Use it when a milestone includes moving parts, joints, actuators, belts, rails, linkages, hinges, sliders, couplers, or robot-style frames.

This skill does not replace CAD generation. It turns geometry and assembly intent into explicit frames, axes, joints, limits, and validation checks that `/cad-spec`, `/assembly-layout`, and `/spec-to-cad` can use.

The core contract is explicit joints, frames, axes, limits, and evidence links.

## Use This Skill When

Use this skill for:

- linear actuators, belt drives, lead screws, rack/pinion systems, hinges, slides, linkages, arms, grippers, carriages, and rotary stages;
- assemblies that need joint axes, travel, limits, or transform chains;
- converting CAD assembly intent into URDF, SDF, SRDF, or simulator/planning handoff notes;
- reviewing whether CONTACT_MAP and CONNECTIONS describe actual motion constraints.

Do not use this skill for static single-body parts unless the user specifically asks for frames or coordinate systems.

## Inputs

Read:

```text
00_requirements/requirements_brief.md
02_parts/selected_parts_manifest.json
02_parts/normalized_step_metadata.json
03_cad/custom_cad_handoff.yaml
03_cad/exports/
04_assembly/contact_map.json
04_assembly/connections.json
05_validation/validation_report.json
```

Use CAD inspection outputs when available: refs, facts, planes, positioning, measure, mate, frame, and diff.

## Kinematic Contract

For each moving interface, define:

- parent part and child part;
- joint type: fixed, revolute, prismatic, continuous, screw, belt-coupled, gear-coupled, compliant, or unknown;
- joint origin/frame;
- axis direction in a stated coordinate system;
- travel or rotation limits;
- nominal position and home/reference state;
- driven/passive status;
- actuator or transmission relation;
- collision/contact expectations;
- evidence check IDs.

Store the result in `04_assembly/connections.json` where possible. If a richer working artifact is needed, keep it near the assembly folder, for example:

```text
04_assembly/kinematic_contract.json
04_assembly/frames.md
04_assembly/urdf_handoff.md
```

## Frame Rules

- Use right-handed coordinate frames unless the project explicitly states otherwise.
- State units.
- Do not infer axes only from a rendered image.
- Tie axes to CAD refs, planes, holes, shafts, rails, or measured geometry.
- Use source-locked part metadata for catalog components when available.
- Mark any guessed frame as `assumed` and non-final.

## Validation Checks

For final motion claims, require evidence for:

- each joint connects known parts;
- each axis is finite, normalized, and tied to geometry or source metadata;
- travel limits are measurable or requirement-backed;
- mating faces, bores, rails, belts, or shafts have geometry evidence;
- moving pairs have clearance/interference checks where in scope;
- no moving part is floating outside the connection graph;
- final report does not claim dynamic simulation unless it actually ran.

Record supporting validation checks with `evidence_type: "kinematic_contract"` or attach the kinematic rows to existing `geometry_inspection` checks through `evidence_check_ids`.

## URDF/SDF/SRDF Boundary

Use URDF/SDF/SRDF only as handoff formats when requested or when the downstream simulator/planner needs them:

- URDF: links, joints, inertial placeholders, visual/collision mesh references, and transforms;
- SDF: simulation/world details, contacts, plugins, and runtime environment assumptions;
- SRDF: semantic groups, planning groups, disabled collisions, end effectors, and named states.

Do not invent masses, inertia tensors, friction, controller gains, collision safety, or planning validity. If unavailable, mark them as placeholders.

## Output

Report:

- kinematic graph summary;
- joint table with parent, child, type, axis, limits, and evidence;
- frame and coordinate assumptions;
- missing geometry/source evidence;
- required updates to CONTACT_MAP, CONNECTIONS, or CAD source;
- smallest unblock steps for final motion claims.

If the assembly is only static, return `No kinematic scope` and explain which evidence proves it is static.
