---
name: interface-signatures
description: Define standard mechanical interface signatures for layout CAD without requiring full supplier geometry. Use for motors, belts, pulleys, bearings, rails, screws, shafts, bolt patterns, envelopes, and reusable mating facts that drive low-detail assembly proxies.
version: 0.8.9
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
2. Check `registry/interfaces/index.json` for a known layout-ready signature.
3. If no exact registry or project model is available, record the miss and proceed with a documented envelope when layout is not fit-critical.
4. Extract only interface facts needed for layout.
5. Mark each fact as standard, assumed, user-provided, or must-confirm.
6. Define envelope geometry when useful.
7. Name checks that can validate the interface in generated CAD.
8. State what a proxy may simplify.
9. State what needs datasheet or supplier evidence before final claims.

## Signature Shape

Use compact Markdown:

```text
Interface signature: <family/name>
- trusted_for_layout: yes
- source: common standard | user-provided | assumed | project registry
- primary axes:
- mounting datums:
- critical dimensions:
- validation targets:
- envelope:
- proxy may simplify:
- must confirm before final:
```

## Non-Negotiables

- Do not invent ratings.
- Do not call a signature supplier-verified.
- Do not let a missing STEP file block layout when the interface signature is enough.
- Do not start broad catalog crawling before trying the built-in registry and documented envelope path.
- Do not use an interface signature for final procurement identity.

## References

- `references/common-families.md` — common component families and the facts usually needed for layout.
- `references/signature-quality.md` — quality labels and finalization boundaries.
