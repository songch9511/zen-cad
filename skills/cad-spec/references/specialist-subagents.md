# Specialist Subagents

Read this when the user asks to continue from spec into CAD work, or when the assembly is complex enough that layout, interfaces, motion, generation, and review should be separated.

## Delegation Rule

Spawn subagents only when the harness supports them and the subtask is bounded. The lead agent keeps ownership of the CAD spec, locked facts, and final user-facing answer.

Good subagent tasks:

- independent enough to run without blocking the lead;
- small enough to return a concrete artifact or review note;
- tied to named spec sections and locked facts;
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
- source paths, generated artifact paths, assumptions, and checks run;
- stop if a locked fact must change.

### CAD Reviewer

Ask for:

- comparison against locked layout facts;
- interface and motion relationship checks;
- drift from the proceed gate;
- allowed versus disallowed simplifications;
- concise blockers and smallest correction steps.

## Lead Reconciliation

After subagents return:

1. Merge only facts that are supported by the spec or clearly marked assumptions.
2. Resolve conflicts in frames, axes, dimensions, or clearances before handoff.
3. Update locked layout facts explicitly.
4. Keep rejected or uncertain facts in open questions.
5. Do not proceed to detail CAD until positioning and interface blockers are resolved.
