# Assembly Positioning

Read this when a design has more than one part, mating geometry, repeated features, motion, or user-visible layout risk.

## Core Rule

Positioning is a source-level design fact, not a visual afterthought. A downstream CAD generator may use build123d joints, explicit transforms, mates, constraints, or another mechanism, but the spec must define the intended frames and relationships before geometry is generated.

## Required Positioning Facts

For each assembly:

- fixed/root component;
- root frame origin and axes;
- part-local frame convention for each positioned part;
- primary datum faces, axes, and centerlines;
- intended contacts, clearances, and offsets;
- moving joints and allowed degrees of freedom;
- repeated component pattern origins and spacing;
- world-frame expectations for critical parts.

## Preferred Relationship Types

Use precise relationship names:

- `flush_plane`: two planes touch with zero or named gap.
- `coaxial`: two cylinders or axes share a centerline.
- `parallel_axes`: axes remain parallel with named offset.
- `centered_on`: one frame or feature is centered on another.
- `pitch_contact`: belt, gear, chain, or sprocket pitch references are tangent/meshed.
- `sliding_on`: carriage, rail, slot, or guide contact with travel range.
- `rotates_about`: shaft, hinge, bearing, or pulley rotation axis.
- `fastened_by`: screw, bolt, pin, insert, clamp, or press fit pattern.

## Locked Layout Facts

Lock only facts that must survive detail modeling:

- root frame;
- part transforms;
- datum frames;
- joint axes;
- center distances;
- pitch references;
- mounting faces;
- bolt patterns;
- bores and shaft diameters;
- rail/slot alignment;
- clearances and keep-outs;
- motion limits.

Do not lock cosmetic fillets, chamfers, tessellation quality, thread detail, tooth surface fidelity, or enclosure curvature unless they control an interface.

## Layout Drift

If detail modeling changes a locked fact, do not patch forward silently. Return to the proceed gate and ask for layout re-approval.
