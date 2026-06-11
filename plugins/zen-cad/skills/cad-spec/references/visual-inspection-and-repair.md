# Visual Inspection And Repair

Read this when generated CAD exists, a viewer or screenshot tool is available, or the user asks the agent to inspect and repair fit, fastening, clearance, mesh, floating bodies, or engineering plausibility.

## Principle

Visual inspection is a discovery mechanism, not final proof. The agent should use screenshots, viewer links, and multi-view snapshots to find likely problems, then convert each concern into a measurable geometry, interface, clearance, mate, or engineering-rule check before claiming it is fixed.

## Required View Packet

For generated assemblies, request or capture enough evidence to inspect the model from more than one angle:

- isometric shaded + wire overview;
- top, front, and right orthographic views;
- close views of fasteners, bearings, shafts, bores, gear or belt meshes, and support brackets;
- section, xray, exploded, or isolated-part views when available and useful;
- before/after snapshots for repair passes.

If the viewer cannot produce a required view, record the view as skipped with a reason and preserve the remaining geometry checks.

## Visual Issue Taxonomy

Classify visual findings with stable issue types:

- `floating_unconstrained_body`: a part appears unsupported, detached, or missing a contact/fastening relationship.
- `unintended_interference`: two solids visibly overlap where no press fit, merge, or boolean union is intended.
- `insufficient_clearance`: visible gap is too small or too large for the stated shaft, bore, fastener, belt, gear, or enclosure relationship.
- `missing_fastener_engagement`: bolt, screw, boss, nut, washer, or mounting hole is absent, misaligned, too shallow, or not long enough to engage.
- `coaxiality_or_plane_misalignment`: shaft/bore axes, bearing seats, pulley planes, rail axes, or mounting datums are visibly off.
- `mesh_or_transmission_error`: gear teeth, belt centerline, pulley pitch plane, chain/sprocket, or linkage relationship is visibly implausible.
- `unsupported_or_implausible_load_path`: thin walls, overhangs, cantilevers, rib placement, or bracket support looks mechanically implausible for the stated role.
- `assembly_order_or_access_issue`: fasteners, shafts, covers, or service features cannot be inserted, removed, or reached in the shown layout.

## Finding Format

Each visual finding should include:

```text
issue_id:
issue_type:
view_or_artifact:
suspected_parts:
locked_fact_refs:
visual_evidence:
measurable_check_to_add:
smallest_repair_candidate:
stop_condition:
```

Use part ids and feature ids from the CAD spec, source, manifest, scene, or viewer hierarchy. Do not describe a repair only as "make it look better"; name the parameter, datum, placement, feature, mate, or clearance to change.

## Engineering Rule Checks

Prefer engineering-rule checks that can be measured or inspected from source:

- fastener axis aligns with hole axis and mounting faces;
- fastener length and boss depth are plausible for engagement;
- shaft diameter is compatible with bore diameter and clearance intent;
- bearing bore axis, shaft axis, and support bore are coaxial;
- pulley or gear pitch planes are coplanar where required;
- gear center distance matches pitch radii and intended mesh;
- belt centerline connects pulley pitch circles without a plane mismatch;
- moving parts have declared travel limits and keep-out clearance;
- body has a support/contact/fastening path back to the root frame;
- wall, rib, boss, and bracket dimensions are nonzero and plausible for layout.

Do not claim load rating, fatigue life, certification, or manufacturing readiness unless a downstream engineering analysis actually ran.

## Visual-To-Measurable Repair Loop

When visual inspection finds a concern:

1. classify the issue using the taxonomy;
2. identify the smallest source-level cause: parameter, placement, datum, feature, interface primitive, or handoff instruction;
3. add or rerun a measurable check that can fail before repair and pass after repair;
4. regenerate the affected CAD artifact;
5. recapture the same view packet or targeted close-up;
6. report before/after evidence, checks rerun, and remaining skipped risks.

If a repair would change a locked layout fact, stop and return to the proceed gate instead of silently adjusting the model.

## Subagent Pattern

For complex generated assemblies, dispatch at least these bounded review roles when subagents are available:

- `visual-reviewer`: inspect the view packet and return visual findings in the required format.
- `engineering-reviewer`: translate findings into measurable checks and engineering-rule concerns.
- `cad-reviewer`: compare repaired outputs against locked facts, parameter contract, and proceed gate.

If subagents are unavailable, the lead must run those roles sequentially and state that fallback explicitly.
