# Inspection And Repair

Read this when CAD generation, review, or detail upgrade is requested.

## Principle

Generated CAD should be checked against the spec, not against visual plausibility alone. Programmatic facts, dimensions, planes, frames, mating deltas, and labels are stronger evidence than screenshots or viewer links. Visual snapshots are useful review aids and should be converted into geometry checks before becoming claims.

## Inspection Plan

Before handoff, state what the downstream generator or reviewer should check:

- artifact exists and is generated from the intended source;
- top-level solids, parts, labels, and assembly children match the spec;
- bounding box, key dimensions, clearances, and center distances are within expected values;
- major planes, axes, bores, shafts, pitch references, and mounting faces are present;
- part-local frames and world placements preserve locked layout facts;
- motion poses, travel limits, gear or belt relationships, and keep-outs are plausible;
- visual snapshot or viewer review is included when the active tool supports it, or skipped with a reason.

## Inspection Hierarchy

Use the strongest available evidence in this order:

1. source-level parameters, datums, joints, and labels;
2. generated artifact facts such as solid counts, labels, bounding boxes, planes, and axes;
3. targeted measurements, mate checks, frame checks, or diffs;
4. visual snapshots or viewer links;
5. prose caveats for checks that could not run.

Do not report a check as passed unless it actually ran or is directly supported by generated source facts.
Do not validate CAD by git diff, file size, screenshot, or viewer link alone.

## Repair Loop

When a check fails:

1. read the failing output or reviewer finding;
2. classify the failure;
3. change the smallest responsible source, parameter, datum, joint, or handoff instruction;
4. regenerate the affected artifact;
5. rerun the failed check and any dependent checks;
6. report remaining risk or deliberate deviations.

Locked layout facts cannot be changed inside the repair loop. If a repair requires changing an approved axis, center distance, mounting face, clearance, or drivetrain relationship, stop and return to the proceed gate.

## Common Failure Classes

- source syntax or import failure;
- invalid, missing, open, or zero-volume geometry;
- wrong scale, unit mismatch, or radius/diameter confusion;
- missing feature, wrong boolean direction, or shallow through-cut;
- selector or label fragility after a topology change;
- positioning mismatch, inverted axis, wrong local datum, or stale transform;
- visual concern that needs a measurement or frame check;
- missing viewer, snapshot, or export capability in the active harness.

## Review Report

Ask the downstream agent to return:

- source path and primary artifact path;
- generation status;
- inspection checks actually run;
- failed or skipped checks with reasons;
- snapshot or viewer link when supported;
- whether the model is ready for proceed review, detail upgrade, or another repair pass.
