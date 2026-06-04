---
name: interface-signatures
description: Define standard mechanical interface signatures for layout CAD without requiring full supplier geometry. Use for motors, belts, pulleys, bearings, rails, screws, shafts, bolt patterns, envelopes, and reusable mating facts that drive low-detail assembly proxies.
version: 0.8.0
---

# Interface Signatures

## Purpose

Use this skill to represent the interface facts of common components before full supplier geometry exists. It supports layout-first CAD by giving the generator trustworthy mating dimensions, axes, envelopes, and clearance assumptions.

This skill does not prove ratings, procurement identity, material, certification, or supplier geometry.

## Use This Skill When

Use it when a layout spec mentions:

- motors, servos, gearmotors, encoders, sensors, or connectors;
- belts, pulleys, gears, sprockets, chains, shafts, bearings, bushings, rails, or screws;
- fasteners, inserts, bolt patterns, clearance holes, counterbores, or standoffs;
- a known family such as NEMA motors, GT2 belts, M-series screws, 608 bearings, or linear rail carriages.

## Workflow

1. Identify the component family.
2. Extract only interface facts needed for layout.
3. Mark each fact as standard, assumed, user-provided, or must-confirm.
4. Define envelope geometry when useful.
5. State what a proxy may simplify.
6. State what needs datasheet or supplier evidence before final claims.

## Signature Shape

Use compact Markdown:

```text
Interface signature: <family/name>
- trusted_for_layout: yes
- source: common standard | user-provided | assumed | project registry
- primary axes:
- mounting datums:
- critical dimensions:
- envelope:
- proxy may simplify:
- must confirm before final:
```

## Non-Negotiables

- Do not invent ratings.
- Do not call a signature supplier-verified.
- Do not let a missing STEP file block layout when the interface signature is enough.
- Do not use an interface signature for final procurement identity.

## References

- `references/common-families.md` — common component families and the facts usually needed for layout.
- `references/signature-quality.md` — quality labels and finalization boundaries.
