# Export Targets

Read this when a CAD spec will be handed to a generator, reviewer, viewer, or downstream packaging step.

## Principle

A CAD spec should state artifact intent before generation starts. The downstream agent should know what source to create, which CAD artifact is primary, which outputs are secondary, and what review evidence is expected.

Zen CAD does not require every environment to use a specific CAD kernel. When build123d is available, Zen CAD can execute generated source into a first-pass STEP artifact itself. When another active tool supports STEP, treat STEP/STP as the primary exchange artifact unless the user asks for a different target.

## Target Maturity

State one maturity target:

- `layout_proxy`: low surface detail, high interface and positioning fidelity;
- `detail_cad`: approved layout with improved surface, feature, and packaging quality;
- `final_package`: requested exports plus completed checks available in the active toolchain.

Do not request final-package polish before the layout proxy has passed the proceed gate.

## Artifact Contract

Include:

- CAD source intent: build123d, CadQuery, FreeCAD, native tool file, or unknown;
- primary artifact: usually STEP/STP when supported;
- secondary artifacts: STL, DXF, 3MF, native GLB, screenshots, or viewer links only when requested or supported;
- review artifacts: deterministic inspection summary, snapshot packet, viewer handoff, or equivalent;
- source-of-truth rule: source and spec remain authoritative; generated files are derived.

## Explicit Targets

Ask downstream generators for explicit file paths when they create files. Avoid vague instructions such as "generate everything in the folder." Do not request directory-wide generation unless the user explicitly asks for batch conversion.

For a new model, the handoff should name:

- source path or source naming intent;
- primary CAD artifact path or naming intent;
- whether Zen CAD should run the build123d generation phase locally;
- whether the spec should carry a native `cad_feature_plan` for holes, bores, patterns, chamfers, fillets, or simplified gears;
- whether a local viewer link should be packaged after STEP generation;
- expected top-level labels or assembly children;
- expected bounding box or critical measurements;
- inspection and snapshot requirements supported by the tool.

## Secondary Outputs

Secondary exports should branch from accepted geometry. Do not let an STL, visual render, or mesh-only output become the source of truth for a mechanical assembly unless the user explicitly chooses that workflow.

If the active tool cannot create a requested secondary export, report the missing capability and keep the primary CAD artifact reviewable. Local viewer links should point at generated CAD artifacts when possible, but they remain review evidence only.
