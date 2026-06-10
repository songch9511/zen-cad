---
name: assembly-layout
description: Define and review low-detail mechanical assembly layouts before detail CAD. Use for assembly graphs, root frames, contact/connection concepts, locked interface facts, positioning review, drivetrain layout review, and proceed-gate readiness.
version: 1.0.1
---

# Assembly Layout

## Purpose

Use this skill to define or review the low-detail assembly contract that should be correct before detail CAD begins. It is narrower than `cad-spec`: it focuses only on how parts locate, mate, move, clear, and connect.

This skill does not generate CAD, source parts, or replace the lead CAD spec.

## Use This Skill When

Use it when a task needs:

- assembly graph definition;
- root frame and part-local frame decisions;
- contacts, connections, joints, clearances, keep-outs, or motion limits;
- proceed review after a layout proxy;
- source-level positioning, measurement, frame, or mate-check expectations;
- drift checks between approved layout and detail CAD.

## Workflow

1. Identify the fixed/root component.
2. Define root frame and part-local frames.
3. List each part's role: structure, locator, driver, driven, guide, fastener, cover, sensor, proxy.
4. Define contacts and connections as relationships, not file-format rows.
5. Name locked facts that detail CAD must preserve.
6. Define measurement, frame, mate, or snapshot checks that can prove positioning.
7. Define the proceed review checklist.
8. If reviewing a generated layout, compare it only against the locked facts and layout intent.

## Relationship Types

Use clear relationship names:

- `contacts`: faces, cylinders, pitch references, keep-out boundaries, or clearance pairs.
- `connections`: fasteners, press fits, bearings, shafts, hinges, belts, gears, rails, sliders, couplers, cables.
- `motion`: revolute, prismatic, cylindrical, belt-coupled, gear-coupled, screw-driven, linkage-driven.

## Non-Negotiables

- Do not approve detail modeling if the assembly graph is still unclear.
- Do not treat a pretty surface as evidence that a mate or drivetrain is correct.
- Do not rely on visual placement alone when a distance, axis, frame, or mating check can be named.
- Do not change locked facts during detail upgrade without returning to layout review.
- Do not require supplier STEP files for layout review when interface signatures are sufficient.

## References

- `references/layout-contract.md` — assembly graph, contact, connection, and locked fact shape.
- `references/review-checklist.md` — proceed review checklist and layout drift checks.
