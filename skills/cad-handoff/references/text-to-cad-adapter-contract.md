# Text-to-CAD Adapter Contract

Read this when an approved Zen CAD detail handoff should become a CAD Skills/text-to-cad downstream bundle.

## Purpose

The adapter turns an approved `handoff_packet` into a small prompt bundle for `$cad` or CAD Skills/text-to-cad. It does not generate CAD. It exists to preserve the approved layout facts, parameter names, required checks, repair policy, and stop conditions across the boundary into the CAD generator.

## Required Input

Use a handoff packet created after proceed approval:

- `kind: handoff_packet`;
- `target_harness: text-to-cad`;
- `target_maturity: detail_cad`;
- locked facts, parameter contract, artifact targets, required checks, repair loop, and stop conditions populated;
- approval markers in `extensions`: `proceed_gate`, `proceed_gate_status`, `proceed_approval`, and `proceed_decision`.

The adapter rejects handoffs that are not targeted at `text-to-cad`, are not detail handoffs, or do not carry approval markers from a ready proceed gate.

## Command

```bash
python3 tools/package_text_to_cad_bundle.py \
  --handoff <detail_handoff.json> \
  --out <text-to-cad-bundle-dir>
```

The recommended upstream flow is:

```bash
python3 tools/run_contract_pipeline.py --package <contract-package> --out <review-dir> --target-harness text-to-cad
python3 tools/approve_proceed_gate.py --proceed-gate <review-dir>/proceed_gate.json --out <approval.json>
python3 tools/run_contract_pipeline.py --package <contract-package> --out <detail-dir> --target-harness text-to-cad --approval <approval.json>
python3 tools/package_text_to_cad_bundle.py --handoff <detail-dir>/detail_handoff.json --out <text-to-cad-bundle-dir>
```

## Bundle Contents

- `handoff_packet.json`: copy of the approved handoff packet and source handoff for locked facts.
- `text_to_cad_prompt.md`: prompt to send to CAD Skills/text-to-cad.
- `adapter_manifest.json`: dependency-free manifest describing the adapter boundary, included files, approval evidence, and expected downstream returns.

## Boundary

The bundle packager must not create or claim:

- CAD source;
- STEP/STP, STL, or other geometry artifacts;
- measurements from a CAD kernel;
- snapshots;
- viewer links;
- engineering certification.

Those are downstream text-to-cad responsibilities. The prompt asks the downstream generator to return generated files, primary artifact path, deterministic checks actually run, skipped checks and reasons, snapshot or viewer evidence when available, repair attempts, known assumptions, and claims not made.

## Stop Rule

If the downstream generator cannot preserve a locked layout fact, it must stop and return to layout review instead of changing the approved fact.
