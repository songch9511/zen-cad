# Harness Briefs

## Codex

Use this when Codex will create or edit source files:

```text
Use the CAD spec below to create a low-detail layout proxy first.
Preserve locked facts exactly.
Use named parameters for critical dimensions, clearances, and motion controls.
Use the available CAD stack in this workspace.
Return source path, primary CAD artifact path, checks run, failed or skipped checks, and limitations.
If a check fails, make the smallest responsible source-level repair, regenerate, and rerun the failed check.
Do not claim final engineering validity.
```

## text-to-cad / $cad

Use this when the `earthtojake/text-to-cad` CAD skill is installed:

```text
Use $cad to generate STEP-first CAD from this CAD-native spec.
Create build123d/Python source when generating new geometry.
Use named parameters, datums, labels, and source-level joints where useful.
Run refs/facts/planes/positioning inspection, plus targeted measure, frame, mate, or diff checks when relevant.
Run snapshot or viewer review when available for visible generated or updated CAD.
Repair the smallest source-level cause of any failed check, then regenerate and rerun dependent checks.
Hand supported artifacts to $cad-viewer when available.
Stop instead of changing locked layout facts.
```

## Generic CAD Generator

Use when the toolchain is unknown:

```text
Generate a low-detail assembly layout from this spec.
Use simple solids for proxies.
Preserve coordinate frames, axes, center distances, mounting faces, pitch references, clearances, and motion relationships.
Use named parameters and return the primary artifact path, inspection evidence, skipped checks, and limitations.
Report any missing information instead of inventing final details.
```
