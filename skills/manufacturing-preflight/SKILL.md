---
name: manufacturing-preflight
description: Preflight Zen CAD milestone artifacts for likely manufacturing handoff issues in STEP, DXF, STL, 3MF, BOM, material, tolerance, fastener, and process assumptions without claiming certification or production approval.
version: 0.6.6
---

# Manufacturing Preflight

## Purpose

`/manufacturing-preflight` checks whether a Zen CAD milestone has enough manufacturing handoff information to discuss fabrication risks. It is a conservative preflight, not manufacturing approval, certification, or supplier acceptance.

Use this after concept/layout CAD exists and before a final report claims that parts are ready for laser cutting, machining, sheet metal, 3D printing, or vendor quoting.

## Use This Skill When

Use this skill for:

- STEP/STP handoff review;
- DXF export review for flat parts;
- STL/3MF printability review;
- BOM and material/process consistency;
- fastener, insert, tapped hole, clearance, bend, slot, and tolerance review;
- final report language around manufacturability.

Do not use it to certify strength, fatigue, safety, compliance, or vendor acceptance.

## Inputs

Read the active milestone:

```text
00_requirements/requirements_brief.md
03_cad/custom_cad_handoff.yaml
03_cad/exports/
04_assembly/contact_map.json
04_assembly/connections.json
05_validation/validation_report.json
06_bom/bom.csv
07_report/final_engineering_report.md
```

Also read `02_parts/selected_parts_manifest.json` when purchased parts or sourced manufacturing services are in scope.

## Process Selection

Classify each custom part by intended process:

- additive: FDM, SLA, SLS, MJF, metal AM;
- subtractive: CNC mill, lathe, router;
- sheet: laser/waterjet/plasma cut, bent sheet metal;
- manual/bench: drill, tap, ream, press-fit, adhesive, assembly;
- unknown: process not specified.

If the process is unknown, report a blocker instead of assuming one.

## Preflight Checks

For every in-scope custom part, check:

- export file exists and matches validation hashes when recorded;
- units and scale are plausible;
- material is stated or explicitly unknown;
- process is stated or explicitly unknown;
- critical dimensions and tolerances are identified;
- holes, slots, wall thickness, fillets, clearances, bend radii, and edge distances are plausible for the claimed process;
- fasteners/inserts/tapped holes agree with BOM and CONNECTIONS;
- mating interfaces have evidence links where final fit is claimed;
- secondary operations are called out;
- process limitations are listed in the final report.

For DXF/flat parts, also check:

- closed profiles;
- duplicate/overlapping lines noted if inspected;
- bend lines separated from cut lines;
- sheet thickness and material specified;
- inside/outside geometry intent clear.

For STL/3MF printing, also check:

- mesh exists and is non-empty;
- orientation/support assumptions stated;
- wall thickness and minimum features reviewed when tooling allows;
- inserts, holes, and post-processing assumptions stated.

## Evidence Contract

Record manufacturing preflight evidence as a supporting validation check when useful:

```json
{
  "check_id": "CHK-MFG-001",
  "name": "Manufacturing preflight",
  "result": "pass|blocked",
  "evidence_type": "manufacturing_preflight",
  "evidence": "Reviewed export files, BOM, material/process assumptions, and known manufacturing limits.",
  "command": {
    "argv": ["manual-review-or-tool-command"],
    "cwd": "<zen-cad-root>",
    "exit_code": 0
  },
  "artifacts": [],
  "limitations": []
}
```

This evidence type can support reporting, but it does not replace `cad_generation`, `step_load`, or `geometry_inspection` for Zen CAD completion PASS.

## Forbidden Claims

Do not claim:

- vendor acceptance;
- production readiness;
- tolerance stack validation;
- strength, fatigue, thermal, vibration, or lifetime validation;
- regulatory or safety certification;
- material authenticity;
- cost or lead time certainty.

Unless those analyses or supplier responses were actually performed and recorded.

## Output

Report:

- process classification by custom part;
- export paths reviewed;
- pass/block findings by part;
- BOM/process mismatches;
- final-report language that must be weakened;
- smallest unblock steps.

Use `Verdict: PREFLIGHT_PASS` only for the limited preflight scope. Use `Verdict: BLOCKED` when a required export, process, material, or critical manufacturing assumption is missing.
