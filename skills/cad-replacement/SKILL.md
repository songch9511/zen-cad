---
name: cad-replacement
description: Replace layout proxy parts with source-locked STEP/STP, user-provided detail CAD, or generated detail candidates while preserving locked facts. Use for step.parts replacement, source-lock alignment, proxy-to-source interface frame mapping, replacement_plan artifacts, datum/mate transform solving, and post-replacement inspection before proceed or final claims.
---

# CAD Replacement

Use this skill after `cad-spec` has produced a layout proxy scene and a part should be replaced by sourced or detailed CAD. The goal is not visual substitution. The goal is to keep the proxy's locked interface facts fixed while replacing its rough geometry.

## Required Workflow

1. Read the CAD spec, layout proxy scene, source-lock evidence, and any detail candidate handoff.
2. Load `references/interface-frame-contract.md` and `references/replacement-plan.md`.
3. Identify the proxy interface frames that drive replacement: mounting planes, bore/shaft axes, bolt patterns, pitch references, clearance envelopes, and motion axes.
4. If required proxy frames are missing or only described in prose, stop and write the missing frame contract before replacing geometry.
5. Resolve the source geometry. Prefer checksum-recorded local STEP/STP from `source_lock_evidence`; use remote locators only as review references unless the task explicitly allows download.
6. Define source interface frames for the sourced/detail geometry. Use family templates only when the template actually covers the source part.
7. Compute replacement placement from frame mapping: `world_source = world_proxy_frame * inverse(source_frame)`.
8. Write or update a `replacement_plan` artifact that names every transform, locked fact, required check, and blocked item.
9. Generate or update CAD source only after the replacement plan is complete.
10. Inspect the transformed geometry against locked facts. Do not proceed on screenshots, file size, bbox-only checks, or apparent visual alignment.

## Hard Rules

- Do not move a locked proxy frame to fit a source STEP.
- Do not silently accept source geometry whose interface frames disagree with the approved layout.
- Do not claim final readiness while replacement alignment, mate, clearance, or source-lock checks are skipped.
- If a source part cannot be aligned without changing a locked fact, return to the proceed gate.

## Outputs

- `interface_frame` artifacts for proxy frames and source/detail frames when they are not already present.
- `replacement_plan` with one replacement entry per part.
- Inspection report that measures post-replacement axes, planes, bolt patterns, clearances, and failed/skipped checks.

## References

- `references/interface-frame-contract.md` — frame fields, tolerances, and source/proxy frame rules.
- `references/replacement-plan.md` — replacement plan status, transform contract, and pass/fail criteria.
