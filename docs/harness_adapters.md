# Harness Adapters

Zen CAD 0.8 is a CAD-native spec skill pack. The harness supplies CAD generation, file edits, terminal execution, viewer links, web access, and worker orchestration. Zen CAD supplies focused skills for writing specs, layout contracts, interface signatures, and downstream CAD handoffs.

## Distribution Surfaces

- `skills/cad-spec`: default entrypoint.
- `skills/assembly-layout`: layout contract and proceed review.
- `skills/interface-signatures`: standard interface facts for layout.
- `skills/cad-handoff`: harness-specific downstream briefs.
- `skills/agentic-cad`: deprecated compatibility shim.
- `plugins/`: thin adapter notes for generic repository-local harnesses.
- `./zen-cad`: legacy milestone/evidence CLI retained during transition.

## Adapter Contract

A harness adapter should:

1. Make the bundled skills discoverable.
2. Start new CAD work through `cad-spec`.
3. Keep harness-specific paths and commands out of the core spec until handoff.
4. Generate a low-detail layout proxy before detail CAD when assembly positioning matters.
5. Preserve locked layout facts after proceed.
6. Use legacy completion gates only when final/release evidence is explicitly in scope.

## text-to-cad Compatibility

When `earthtojake/text-to-cad` or `$cad` is installed:

- use Zen CAD to write the spec and locked layout facts;
- hand the spec to `$cad` for STEP-first generation and inspection;
- use CAD Viewer and snapshots for review when available;
- do not ask `$cad` to perform sourcing, BOM, or final evidence work during layout.
