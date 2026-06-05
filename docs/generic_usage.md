# Generic Usage

Zen CAD 0.8 can be used in any agentic environment that can read Markdown and hand work to a CAD-generation toolchain.

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

Run `python3 tools/validate_contract.py` to verify the built-in schema and registry surface. Pass `--package <path>` to also check a generated contract package before CAD generation or review handoff.

Run `python3 tools/generate_layout_proxy.py --package <path> --out <dir>` after validation to produce a kernel-neutral `layout_proxy.scene.json` plus an inspection report skeleton. This is a layout contract artifact for downstream CAD generation, not a STEP export.

Run `python3 tools/inspect_layout_proxy.py --package <path> --scene <scene.json> --out <report.json>` to check whether a layout proxy scene carries the expected locked facts, part primitives, relationships, and interface datums before handing it to a CAD exporter.
