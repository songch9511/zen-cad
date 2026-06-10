# Parameter Contract

Read this when a CAD spec has dimensions, repeated features, motion controls, configurable variants, or downstream CAD generation.

## Principle

Parameters are part of the model contract. They should make design intent traceable from the user's prose to generated geometry, inspection targets, and later detail upgrades.

A good parameter says what it controls, which facts it must preserve, and how the generated CAD can prove it behaved correctly.

## Required Parameter Fields

Use a compact Markdown table or bullet list with these fields:

- name;
- units or dimensionless status;
- default or selected value;
- allowed range when meaningful;
- locked status: locked, assumed, or derived;
- source: user, standard default, derived constraint, or temporary layout assumption;
- drives: named part, feature, datum, interface, joint, clearance, or motion;
- validation: expected bounding box, distance, mate, frame, angle, count, or visual review.

## Naming

Use semantic names:

- `wall_thickness`, `bearing_clearance`, `hinge_angle_deg`, `gear_ratio`, `bolt_circle_diameter`;
- `rail_spacing`, `shaft_center_distance`, `lid_gap`, `travel_limit`, `tooth_count`.

Avoid untraceable names such as `offset2`, `magic_scale`, `fix_angle`, or `temp_shift` unless the user's source already uses that term.

Encode units in the name only when ambiguity is likely, especially angle, time, clearance, and normalized travel.

## Independent And Derived Values

Separate user-controlled inputs from derived constraints.

For assemblies and mechanisms, derive placement from:

- pivots, axes, centers, and part-local frames;
- link lengths, pitch circles, belt pitch lines, screw pitch, rail spacing, and mounting faces;
- clearances, gasket gaps, bearing seats, shaft bores, and fastener patterns.

Do not tune transforms by sight. If a parameter changes an assembly position, the spec must state the datum or constraint that recomputes the position.

## Layout Versus Detail

Layout parameters may control simplified boxes, cylinders, envelopes, and proxy teeth. Detail parameters may later refine fillets, wall transitions, tooth profiles, chamfers, rib shapes, or cosmetic surfaces.

Do not let detail parameters change locked layout facts. If a detail change needs a new center distance, bore axis, pitch reference, mounting face, or motion limit, return to the proceed gate.

## Parameter Review

Before CAD generation, check:

- every locked fact is represented by a parameter, datum, or explicit relationship;
- every repeated feature is derived from count, pitch, radius, offset, or pattern axis;
- every moving relationship has a pose or travel parameter;
- assumptions are marked as not locked;
- validation targets cover default values and important boundary poses.
