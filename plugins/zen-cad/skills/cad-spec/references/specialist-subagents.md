# Specialist Subagents

Read this when the user asks to continue from spec into CAD work, or when the assembly is complex enough that layout, parameters, interfaces, motion, generation, inspection, and review should be separated.

## Delegation Rule

Spawn subagents only when the harness supports them and the subtask is bounded. The lead agent keeps ownership of the CAD spec, locked facts, and final user-facing answer.

For generated CAD or repair tasks, the lead must create a Subagent Dispatch Plan before editing geometry. If subagents are available, spawn the planned roles. If they are not available, state `Subagent status: unavailable; using sequential fallback roles` and run the same roles sequentially in this order: layout, interface, parameter, motion, CAD generation, visual review, engineering review, CAD review, then repair.

Good subagent tasks:

- independent enough to run without blocking the lead;
- small enough to return a concrete artifact or review note;
- tied to named spec sections and locked facts;
- tied to expected parameters, artifacts, or checks;
- limited to one specialty.

Poor subagent tasks:

- "make the whole CAD";
- open-ended catalog crawling;
- vague quality review without locked facts;
- any task that can silently change approved layout facts.

## Recommended Roles

### Layout Specialist

Ask for:

- root component and root frame;
- part-local frames;
- assembly graph;
- contact and connection relationships;
- locked layout facts;
- proceed-gate review notes.

### Interface Specialist

Ask for:

- interface signatures for common component families;
- mounting faces, bolt patterns, bores, shafts, rails, belts, envelopes;
- assumptions labeled `trusted_for_layout`, `must_confirm_before_detail`, or `must_confirm_before_final`;
- facts that should not block layout proxy generation.

### Parameter Specialist

Ask for:

- named dimensions and motion controls;
- units, default values, allowed ranges, and locked/assumed/derived status;
- which part, feature, datum, joint, or clearance each parameter drives;
- validation targets for critical parameters;
- derived relationships that should replace visual tuning.

### Motion Specialist

Ask for:

- joint types and axes;
- travel limits;
- gear, belt, screw, linkage, or coupler relationships;
- keep-outs and collision-sensitive envelopes;
- drivetrain facts that must be locked before detail modeling.

### CAD Generator

Ask for:

- low-detail layout proxy first;
- simple solids where surface fidelity is not important;
- explicit preservation of locked layout facts;
- source path, primary artifact path, assumptions, and checks run;
- stop if a locked fact must change.

### Inspection Specialist

Ask for:

- source-level parameter and label checks;
- generated artifact facts, bounding boxes, planes, and axes;
- targeted measurements, frame checks, mate checks, or diffs where supported;
- snapshot or viewer review when available;
- failed/skipped checks with reasons and smallest repair step.

### Visual Reviewer

Ask for:

- multi-view snapshot review using isometric, orthographic, close-up, xray, section, or isolated views when available;
- floating body, unintended interference, clearance, fastening, mesh/alignment, and implausible load-path findings;
- issue ids, suspected part ids, view/artifact references, and visual evidence;
- a measurable check that should be added or rerun for each visual concern.

### Engineering Reviewer

Ask for:

- fastener engagement, boss depth, shaft/bore fit, bearing coaxiality, pulley/gear pitch plane, gear center distance, belt centerline, wall thickness, support, and assembly access concerns;
- engineering-rule checks that can be evaluated from source parameters, STEP facts, or targeted measurements;
- repair candidates that change the smallest source-level parameter, datum, placement, feature, or mate;
- stop conditions when a repair would change locked layout facts.

### CAD Reviewer

Ask for:

- comparison against the parameter contract and inspection plan;
- comparison against locked layout facts;
- interface and motion relationship checks;
- drift from the proceed gate;
- allowed versus disallowed simplifications;
- concise blockers and smallest correction steps.

## Lead Reconciliation

After subagents return:

1. Merge only facts that are supported by the spec or clearly marked assumptions.
2. Resolve conflicts in frames, axes, dimensions, or clearances before handoff.
3. Merge the parameter contract, artifact targets, inspection plan, and repair rules.
4. Update locked layout facts explicitly.
5. Keep rejected or uncertain facts in open questions.
6. Do not proceed to detail CAD until positioning, interface, and inspection blockers are resolved.
