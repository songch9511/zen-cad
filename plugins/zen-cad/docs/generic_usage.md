# Generic Usage

Zen CAD 1.0 can be used in any agentic environment that can read Markdown and hand work to a CAD-generation toolchain. The product version is 1.0.0, while contract documents continue to use `schema_version: 0.8.0` for compatibility.

Start with:

```text
Use skills/cad-spec/SKILL.md to write a CAD-native spec for: <goal>
```

When installed as a Codex plugin, use `/cad-spec` directly. Project connection alone does not
register slash skills; install the local `zen-cad` plugin from `.codex-plugin/marketplace.json`
and start a new chat after installation.

If the user asks to continue into CAD generation, keep `cad-spec` as the lead workflow and delegate bounded specialist tasks when the harness supports subagents:

- layout contract review;
- parameter contract review;
- interface signature extraction;
- motion and drivetrain relationship checks;
- layout proxy generation;
- generated artifact inspection;
- repair-loop review;
- generated CAD review against locked facts.

Use `skills/cad-handoff/SKILL.md` when the active generator needs a concise task brief.

Use `schemas/` when a harness needs machine-readable contracts, and use `registry/interfaces/` when a layout proxy needs known component interface facts without catalog crawling. For final-stage standard/catalog part sourcing, use `schemas/source_lock_evidence.schema.json` and `tools/generate_source_lock_evidence.py` to record explicit step.parts, manufacturer, datasheet, project-file, or user-provided evidence separately from layout interface signatures. When that evidence includes a STEP/STP geometry reference, `tools/export_cad_source.py` imports the sourced part into generated build123d source and removes the matching proxy primitives.

Run the contract pipeline runner after a contract package exists:

```bash
python3 tools/run_contract_pipeline.py --package <path> --out <dir>
```

The runner verifies the built-in schema and registry surface, validates the package, creates a kernel-neutral `layout_proxy.scene.json`, inspects scene carry-through, exports CAD source intent, imports source-locked STEP/STP parts when geometry references exist, inspects source carry-through, packages proceed review, and writes a machine-readable `review_bundle.json`.

For a viewer-oriented downstream review, package the proceed gate into a Markdown brief:

```bash
python3 tools/package_viewer_review.py --proceed-gate <dir>/proceed_gate.json --pipeline-run <dir>/pipeline_run.json --out <dir>/viewer_review.md
```

Add `--viewer-artifact <path>` for saved screenshots, viewer pages, GLB/STL/3MF models, or viewer-side reports. The brief treats those files as review aids only; completion evidence still comes from the proceed gate status, inspection reports, locked facts, and downstream geometry measurements.

After the user approves the layout, record the decision and run the detail handoff stage:

```bash
python3 tools/approve_proceed_gate.py --proceed-gate <dir>/proceed_gate.json --out <approval.json>
python3 tools/run_contract_pipeline.py --package <path> --out <detail-dir> --target-harness text-to-cad --approval <approval.json>
python3 tools/package_text_to_cad_bundle.py --handoff <detail-dir>/detail_handoff.json --out <text-to-cad-bundle-dir>
```

For CAD Skills/text-to-cad, the bundle contains `text_to_cad_prompt.md`, `handoff_packet.json`, and `adapter_manifest.json`. The bundle is a downstream contract and prompt only; CAD source, STEP export, geometry checks, snapshots, and viewer links remain text-to-cad responsibilities.

The phase tools remain available for focused diagnosis:

- `tools/validate_contract.py`;
- `tools/generate_layout_proxy.py`;
- `tools/inspect_layout_proxy.py`;
- `tools/export_cad_source.py`;
- `tools/inspect_cad_source.py`;
- `tools/package_proceed_gate.py`;
- `tools/package_review_bundle.py`;
- `tools/package_viewer_review.py`;
- `tools/approve_proceed_gate.py`;
- `tools/generate_detail_handoff.py`;
- `tools/package_text_to_cad_bundle.py`;
- `tools/generate_source_lock_evidence.py`.

These tools keep Zen CAD kernel-neutral. They do not replace downstream CAD generation, STEP export, geometry measurement, source import checks, or engineering certification.
