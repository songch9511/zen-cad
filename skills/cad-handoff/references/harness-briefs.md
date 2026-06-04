# Harness Briefs

## Codex

Use this when Codex will create or edit source files:

```text
Use the CAD spec below to create a low-detail layout proxy first.
Preserve locked facts exactly.
Use the available CAD stack in this workspace.
Return source path, primary CAD artifact path, checks run, and limitations.
Do not claim final engineering validity.
```

## text-to-cad / $cad

Use this when the `earthtojake/text-to-cad` CAD skill is installed:

```text
Use $cad to generate STEP-first CAD from this CAD-native spec.
Create build123d/Python source when generating new geometry.
Use named datums, labels, and source-level joints where useful.
Run refs/facts/planes/positioning inspection when available.
Hand supported artifacts to $cad-viewer when available.
```

## Generic CAD Generator

Use when the toolchain is unknown:

```text
Generate a low-detail assembly layout from this spec.
Use simple solids for proxies.
Preserve coordinate frames, axes, center distances, mounting faces, pitch references, clearances, and motion relationships.
Report any missing information instead of inventing final details.
```
