# Downstream CAD Handoff

Read this when handing a CAD-native spec to Codex, CoBrA, `$cad`, text-to-cad, build123d, CadQuery, FreeCAD, or another generator.

## Handoff Rule

The handoff should tell the generator what to build and what not to optimize yet.

For layout:

```text
Generate a low-detail layout proxy from this spec. Preserve all locked interface facts, coordinate frames, axes, center distances, pitch references, clearances, and motion relationships. Simplify surface detail aggressively. Return artifacts suitable for proceed review.
```

For detail:

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
- validation/review expectations;
- locked facts;
- proxy simplifications allowed;
- unresolved assumptions.

## Codex Handoff

Codex can edit files and run local tools. Ask it to:

- create or update explicit CAD source;
- keep the spec and generated source separate;
- run available deterministic checks;
- return artifact paths and limitations;
- avoid final claims unless final evidence is explicitly requested.

## CoBrA Handoff

CoBrA may invoke installed skills from a workspace unrelated to the project root. Include absolute project paths when paths matter. Keep this detail in the handoff, not in the core spec.

## text-to-cad / `$cad` Handoff

When `$cad` from `earthtojake/text-to-cad` is available, hand it the spec and ask for:

- STEP-first output;
- build123d/Python source when generating new geometry;
- named datums, labels, or source-level joints where useful;
- `scripts/inspect refs --facts --planes --positioning` or equivalent inspection;
- CAD Viewer handoff when available.

Do not require `$cad` to perform sourcing, BOM, final engineering reports, or procurement evidence for layout work.
