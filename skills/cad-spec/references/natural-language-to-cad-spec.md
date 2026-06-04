# Natural Language To CAD Spec

Read this when converting a user's prose into a CAD-native spec. Do not require the user to provide JSON, YAML, or a formal requirements document.

## Goal

Extract the mechanical facts that control CAD generation:

- object or assembly being modeled;
- intended first-pass maturity: layout proxy, detail, or final handoff;
- units and coordinate assumptions;
- functional parts and repeated families;
- fixed and moving relationships;
- critical dimensions, missing dimensions, and safe assumptions;
- interfaces that locate parts;
- motion or drivetrain behavior;
- validation or user-review targets.

## Spec Style

Write Markdown with clear section headings. Use tables when many parts or interfaces must be compared. Use compact structured bullets for geometry facts.

Good:

```text
- Motor shaft axis: +X, origin at motor face center.
- Pulley pitch plane: XZ plane at Y = 0, centered on shaft axis.
- Belt span: upper/lower straight spans parallel to X.
```

Weak:

```text
- Put the pulley on the motor and route the belt around it.
```

## Clarification Policy

Ask one focused question only when:

- no physical scale is provided;
- a mating interface is named but its geometry is unknown;
- a motion range, travel, ratio, or axis is impossible to infer;
- the design is safety-critical, load-bearing, pressure-bearing, medical, or compliance-bound;
- a downstream output depends on an absent source file.

Otherwise proceed with explicit assumptions. Mark each assumption as one of:

- `layout_assumption`: acceptable for first-pass layout;
- `must_confirm_before_detail`: can affect detail CAD;
- `must_confirm_before_final`: affects sourcing, rating, manufacturing, or final claims.

## Internal Readiness Check

Before handing off to CAD generation, confirm the spec names:

- root frame;
- units;
- fixed component;
- part list;
- interface primitives for all positioning-sensitive relationships;
- proxy fidelity policy;
- locked layout facts;
- proceed gate.

If any of these are missing, the spec is not ready for layout CAD.
