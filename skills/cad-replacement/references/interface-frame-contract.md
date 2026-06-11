# Interface Frame Contract

An interface frame is the machine-readable anchor that makes proxy replacement possible. It is stronger than a prose datum statement and weaker than final engineering certification.

## Required Frame Fields

Every replacement-critical frame should name:

- `id`: stable frame id such as `bearing_proxy.bore_frame`;
- `part_id`: the proxy/source/detail part it belongs to;
- `role`: mounting plane, bore axis, shaft axis, bolt pattern, pitch reference, clearance envelope, motion axis, or custom;
- `frame.origin`: XYZ origin in millimeters;
- `frame.x_axis`, `frame.y_axis`, `frame.z_axis`: unit basis vectors;
- `locked_fact_refs`: the locked facts this frame preserves;
- `tolerance`: position, angle, and optional diameter/clearance tolerances.

Use `schemas/interface_frame.schema.json` for standalone frame artifacts.

## Proxy Frames

Proxy frames come from the approved layout contract and are hard constraints after proceed approval. They should be generated from interface signatures, layout parameters, and locked facts, not from visual guessing.

If a proxy frame is missing for a replacement-critical fact, block replacement and repair the contract first.

## Source Frames

Source frames describe the matching interface on a sourced STEP/STP or detail CAD candidate. They can come from:

- explicit user-provided frame metadata;
- source-lock evidence extensions;
- family templates for known parts such as bearings, NEMA motors, rails, pulleys, gears, and fasteners;
- measured geometry from an imported STEP when the active CAD harness can inspect faces, cylinders, and patterns.

Do not assume a source STEP origin is the desired assembly placement.

## Alignment Rule

For each replacement, compute:

```text
world_source = world_proxy_frame * inverse(source_frame)
```

When multiple frames constrain the same replacement, solve the best transform and report residuals. A residual over tolerance blocks proceed.

## Required Checks

Minimum checks after transformation:

- frame origin delta within `position_mm`;
- axis angle delta within `angle_deg`;
- bore/shaft/pitch/bolt dimensions within declared tolerance;
- clearance envelopes still satisfied;
- relationships depending on the part still reference the same locked facts.
