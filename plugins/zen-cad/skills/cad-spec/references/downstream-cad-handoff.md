# Downstream CAD Handoff

Read this when handing a CAD-native spec to the active CAD harness, `$cad`, text-to-cad, build123d, CadQuery, FreeCAD, or another generator.

## Handoff Rule

The handoff should tell the generator what to build and what not to optimize yet.

For layout:

```text
Generate a low-detail layout proxy from this spec. Preserve all locked interface facts, coordinate frames, axes, center distances, pitch references, clearances, and motion relationships. Simplify surface detail aggressively. Return artifacts suitable for proceed review.
Use named parameters for critical dimensions and return checks that prove the locked facts survived generation.
```

For detail after explicit proceed approval:

```text
Upgrade visual and manufacturing-relevant detail while preserving the approved locked layout facts. If any locked fact must change, stop and return to layout review.
```

## Handoff Fields

Include:

- target harness or tool if known;
- target output type: layout proxy, detail model, final package;
- source/spec path or pasted spec;
- desired CAD source format;
- primary output artifact;
- secondary outputs only when requested or supported;
- parameter contract;
- validation/review expectations;
- repair loop expectations;
- locked facts;
- proxy simplifications allowed;
- unresolved assumptions.

## Codex Handoff

Codex can edit files and run local tools. Ask it to:

- create or update explicit CAD source;
- keep the spec and generated source separate;
- preserve named parameters and derived relationships;
- run available deterministic checks;
- return artifact paths, checks run, skipped checks, repair attempts, and limitations;
- avoid final claims unless the required final checks are explicitly requested and completed.

## text-to-cad / `$cad` Handoff

When `$cad` from `earthtojake/text-to-cad` is available, hand it the spec and ask for:

- STEP-first output;
- build123d/Python source when generating new geometry;
- named parameters, datums, labels, or source-level joints where useful;
- `scripts/inspect refs --facts --planes --positioning` or equivalent inspection;
- targeted measurements, frames, mating deltas, diffs, or snapshot review when relevant and supported;
- CAD Viewer handoff when available.

Do not require `$cad` to perform sourcing, BOM, final engineering reports, or procurement evidence for layout work.
