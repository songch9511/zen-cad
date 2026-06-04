# Zen CAD

Harness-native CAD specification skills for agentic mechanical design.

[![Version](https://img.shields.io/badge/version-0.8.0-4A5568?style=for-the-badge)](VERSION)
[![Spec First](https://img.shields.io/badge/CAD--native-spec--first-00A676?style=for-the-badge)](skills/cad-spec/SKILL.md)
[![Assembly First](https://img.shields.io/badge/assembly--first-layout-2F80ED?style=for-the-badge)](skills/assembly-layout/SKILL.md)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

Zen CAD is a compact skill pack for getting better first-pass CAD from agentic harnesses. It is not a CAD kernel, part catalog crawler, validation server, or one-shot text-to-CAD model.

The workflow is:

1. Turn the user's natural-language request into a CAD-native spec.
2. Define named parameters, artifact targets, inspection checks, and repair rules before generation.
3. Lock coordinate frames, datums, interface primitives, motion relationships, and proxy fidelity.
4. Use specialist subagents when the harness supports them: layout, parameters, interfaces, motion, CAD generation, inspection, and review.
5. Generate a low-detail layout proxy whose assembly positioning is correct before surface quality is high.
6. Inspect, repair, and rerun checks against locked facts.
7. Proceed to detail CAD only after the user approves the assembly contract.

## Skills

| Skill | Summary |
| --- | --- |
| [`cad-spec`](skills/cad-spec/SKILL.md) | Default entrypoint. Writes CAD-native specs and orchestrates specialist subagents for layout, parameters, interface, motion, handoff, generation, inspection, and review work. |
| [`assembly-layout`](skills/assembly-layout/SKILL.md) | Defines and reviews root frames, assembly graphs, contacts, connections, motion relationships, locked facts, and proceed readiness. |
| [`interface-signatures`](skills/interface-signatures/SKILL.md) | Captures layout-ready interface facts for common component families without requiring full supplier geometry. |
| [`cad-handoff`](skills/cad-handoff/SKILL.md) | Converts an approved spec into a concise downstream brief for the active CAD generator. |

## Recommended Prompt

```text
Use $cad-spec to turn this mechanical request into a CAD-native layout spec:
<request>

If CAD generation is requested, spawn specialist subagents for layout, parameters, interfaces, motion/drivetrain, CAD generation, inspection, and review where the harness supports delegation.
```

## Development Checks

```bash
python3 -m unittest discover -s tests
```

No example CAD specs are committed. Spec examples should be temporary test fixtures or separately curated artifacts.
