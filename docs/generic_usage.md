# Generic Usage

Zen CAD 0.9 can be used in any agentic environment that can read Markdown and hand work to a CAD-generation toolchain. The product version is 0.9.0, while contract documents continue to use `schema_version: 0.8.0` for compatibility.

Start with:

```text
Use skills/cad-spec/SKILL.md to write a CAD-native spec for: <goal>
```

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

Use `schemas/` when a harness needs machine-readable contracts, and use `registry/interfaces/` when a layout proxy needs known component interface facts without catalog crawling.

Run the 0.9.0 contract pipeline runner after a contract package exists:

```bash
python3 tools/run_contract_pipeline.py --package <path> --out <dir>
```

The runner verifies the built-in schema and registry surface, validates the package, creates a kernel-neutral `layout_proxy.scene.json`, inspects scene carry-through, exports CAD source intent, inspects source carry-through, and packages proceed review.

After the user approves the layout, record the decision and run the detail handoff stage:

```bash
python3 tools/approve_proceed_gate.py --proceed-gate <dir>/proceed_gate.json --out <approval.json>
python3 tools/run_contract_pipeline.py --package <path> --out <detail-dir> --approval <approval.json>
```

The phase tools remain available for focused diagnosis:

- `tools/validate_contract.py`;
- `tools/generate_layout_proxy.py`;
- `tools/inspect_layout_proxy.py`;
- `tools/export_cad_source.py`;
- `tools/inspect_cad_source.py`;
- `tools/package_proceed_gate.py`;
- `tools/approve_proceed_gate.py`;
- `tools/generate_detail_handoff.py`.

These tools keep Zen CAD kernel-neutral. They do not replace downstream CAD generation, STEP export, or geometry measurement.
