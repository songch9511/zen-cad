# Harness Briefs

## Codex

Use this when Codex will create or edit source files:

```text
Use the CAD spec below to create a low-detail layout proxy first.
Preserve locked facts exactly.
Use named parameters for critical dimensions, clearances, and motion controls.
Use the available CAD stack in this workspace.
Return source path, primary CAD artifact path, checks run, failed or skipped checks, and limitations.
Return source-of-truth, generated files, repair attempts, and claims not made.
If a check fails, make the smallest responsible source-level repair, regenerate, and rerun the failed check.
Do not claim final engineering validity.
```

## text-to-cad / $cad

Use this when the `earthtojake/text-to-cad` CAD skill is installed:

```text
Use $cad to generate STEP-first CAD from this CAD-native spec.
Create build123d/Python source when generating new geometry.
Use named parameters, datums, labels, and source-level joints where useful.
Run deterministic geometry inspection first: refs/facts/planes/positioning plus targeted measure, frame, mate, or diff checks when relevant.
If visible primary CAD was created or updated and snapshot/viewer tooling is available, return saved snapshots or viewer links; if skipped, state why.
Do not treat viewer links or screenshots as substitutes for geometry checks.
Repair the smallest source-level cause of any failed check, then regenerate and rerun dependent checks.
Hand supported artifacts to $cad-viewer when available.
Stop instead of changing locked layout facts.
```

When a Zen CAD `handoff_packet` already exists from an approved proceed gate, package the downstream prompt bundle instead of asking Zen CAD to generate CAD:

```bash
python3 tools/package_text_to_cad_bundle.py --handoff <detail_handoff.json> --out <text-to-cad-bundle-dir>
```

Send `text_to_cad_prompt.md` and `handoff_packet.json` to CAD Skills/text-to-cad. The bundle manifest records that Zen CAD did not create CAD source, STEP/STP geometry, snapshots, or viewer links in this adapter step.

## Generic CAD Generator

Use when the toolchain is unknown:

```text
Generate a low-detail assembly layout from this spec.
Use simple solids for proxies.
Preserve coordinate frames, axes, center distances, mounting faces, pitch references, clearances, and motion relationships.
Use named parameters and return the primary artifact path, inspection evidence, skipped checks, and limitations.
State generated files as derived artifacts and identify the source/spec as authoritative.
Report any missing information instead of inventing final details.
```
