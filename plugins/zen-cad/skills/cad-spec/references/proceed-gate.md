# Proceed Gate

Read this when the spec will be used to generate a layout proxy before detail modeling.

## Purpose

The proceed gate is the UX checkpoint between low-detail layout and high-detail CAD. It tells the user exactly what to inspect before approving detail work.

## Gate Content

Write a proceed gate with:

- layout verdict target: `ready_for_review`, `needs_clarification`, or `blocked`;
- inspection checklist;
- locked facts that will be preserved after approval;
- allowed detail-stage changes;
- changes that require returning to layout;
- known assumptions and unresolved risks.

## User-Facing Prompt

Use direct language:

```text
Review the rough layout for positioning, interfaces, and drivetrain structure.
If the axes, center distances, belt/gear/rail relationships, clearances, and mounting faces are correct, say "proceed" and detail modeling can preserve these locked facts.
```

Do not ask the user to approve surface quality during layout unless surface quality controls an interface.

## Approval Record

If the harness has a project file, write the approved locked facts there. If no project file exists, include them in the conversation handoff. When using the repo runtime, record the decision as a `proceed_approval` artifact before generating a detail handoff. The important part is that detail generation receives the locked facts explicitly and can prove they match the reviewed proceed package.

## Return To Layout

Return to layout review when detail modeling would change:

- root frame;
- part transforms;
- joint axes;
- center distances;
- pitch references;
- belt plane;
- mounting face positions;
- bolt pattern positions;
- clearance envelopes;
- travel range;
- part count or assembly graph.

Detail modeling may change visual fidelity, supplier body contours, fillets, chamfers, threads, labels, and secondary exports if locked facts remain unchanged.
