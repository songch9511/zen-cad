# Signature Quality

Use quality labels so downstream CAD understands how much to trust an interface signature.

## Labels

- `standard`: common standard dimensions are stable enough for layout.
- `user_provided`: user supplied a drawing, dimensions, file, or explicit part.
- `project_registry`: local project data provides dimensions.
- `assumed`: chosen for first-pass layout only.
- `must_confirm`: do not use for detail/final without confirmation.

## Layout Acceptance

A signature is layout-ready when it defines the interfaces that locate the part:

- mounting datum;
- primary axis;
- mating dimensions;
- envelope or keep-out;
- assumptions that could affect detail.

## Final Boundary

An interface signature is not final evidence. Before final claims, the project may need:

- source-locked supplier or manufacturer identity;
- exact part number or SKU;
- datasheet;
- cached STEP/STP;
- rating evidence;
- command-backed geometry inspection.

Keep this boundary explicit so layout work can move without pretending to be procurement-ready.
