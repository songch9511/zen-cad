# Zen CAD

Harness-native CAD specification skills for agentic mechanical design.

[![Version](https://img.shields.io/badge/version-0.8.0-4A5568?style=for-the-badge)](VERSION)
[![Spec First](https://img.shields.io/badge/CAD--native-spec--first-00A676?style=for-the-badge)](skills/cad-spec/SKILL.md)
[![Assembly First](https://img.shields.io/badge/assembly--first-layout-2F80ED?style=for-the-badge)](skills/assembly-layout/SKILL.md)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

## Overview

Zen CAD 0.8.0 is a skill pack for writing better CAD-generation briefs. It is not a CAD kernel, STEP part search engine, validation server, or one-shot text-to-CAD model.

The core idea is simple:

1. Convert a natural-language mechanical request into a CAD-native spec.
2. Define coordinate frames, datums, interface primitives, motion relationships, and locked layout facts before generation.
3. Ask the active CAD harness, `$cad`, text-to-cad, build123d, CadQuery, FreeCAD, or another generator to create a low-detail `layout_proxy`.
4. Let the user review positioning, connections, and drivetrain structure while detail is still cheap.
5. Proceed to detail CAD only after the assembly contract is approved.

The first CAD artifact should not be judged by surface polish. It should be judged by whether the assembly's axes, mating primitives, center distances, clearances, belt/gear/rail relationships, and fixed/moving structure are correct.

## Skills

| Skill | Summary |
| --- | --- |
| [`cad-spec`](skills/cad-spec/SKILL.md) | Core 0.8 skill. Turns prose into a CAD-native spec with coordinate frames, interface primitives, locked facts, proxy fidelity boundaries, proceed gate, and downstream CAD handoff. |
| [`assembly-layout`](skills/assembly-layout/SKILL.md) | Defines and reviews low-detail assembly layout contracts: root frames, contacts, connections, motion relationships, locked facts, and proceed review checklists. |
| [`interface-signatures`](skills/interface-signatures/SKILL.md) | Defines layout-ready interface signatures for common component families without requiring full source-locked STEP geometry. |
| [`cad-handoff`](skills/cad-handoff/SKILL.md) | Converts a CAD-native spec into a concise downstream brief for the active CAD harness, `$cad`, text-to-cad, build123d, or another CAD generator. |
| [`agentic-cad`](skills/agentic-cad/SKILL.md) | Deprecated compatibility entrypoint. Route new work to `cad-spec` plus focused companion skills. |

Legacy 0.7 skills for source-lock, spec-to-CAD execution, kinematics, artifact review, manufacturing preflight, and producer/verifier loops remain in the repository while the 0.8 spec-first architecture is introduced.

## Recommended Flow

Use `cad-spec` first:

```text
Use $cad-spec to turn this mechanical request into a CAD-native layout spec:
<request>
```

The spec should include:

- intent;
- units and coordinate system;
- parts and roles;
- assembly graph;
- interface primitives;
- motion and drivetrain relationships;
- proxy fidelity policy;
- locked layout facts;
- assumptions and open questions;
- proceed gate;
- downstream CAD handoff.

Then hand off to the active CAD harness:

```text
Use $cad-handoff to generate a layout brief for the active CAD harness from this spec.
```

The CAD generator should create a low-detail layout proxy first. It may simplify teeth, fillets, threads, supplier body contours, cable sweeps, and cosmetic surfaces. It must preserve locked facts such as axes, datums, mounting faces, bores, pitch references, center distances, clearances, and motion relationships.

## Proceed Gate

The user's approval point should be explicit:

```text
Review the rough layout for positioning, interfaces, and drivetrain structure.
If the axes, center distances, belt/gear/rail relationships, clearances, and mounting faces are correct, say "proceed" and detail modeling can preserve these locked facts.
```

After proceed, detail CAD may improve surface fidelity and replace proxies, but it must not change locked layout facts without returning to layout review.

## Relationship To text-to-cad

Zen CAD 0.8 is intended to sit in front of CAD-generation tools such as [earthtojake/text-to-cad](https://github.com/earthtojake/text-to-cad). `text-to-cad` provides practical CAD generation, inspection, viewer, and STEP workflows. Zen CAD provides the spec discipline that makes those generators more likely to produce correct assemblies on the first layout pass.

Use `$cad` from text-to-cad when available for STEP-first generation and inspection. Use Zen CAD skills to write the CAD-native spec, interface signatures, layout contract, proceed gate, and downstream handoff.

## Legacy CLI

The repository still includes the 0.7 milestone/evidence CLI:

```bash
./zen-cad doctor
./zen-cad new "<goal>"
./zen-cad validate --level structure milestones/<id>
./zen-cad validate --level completion milestones/<id>
```

Treat this CLI as a legacy compatibility harness during the 0.8 transition. It is useful for existing milestone demos and final-evidence experiments, but it is not the core 0.8 user experience.

## Development Checks

Run:

```bash
python3 -m unittest discover -s tests
./zen-cad doctor
./zen-cad validate
```

No example CAD specs are committed in 0.8. Spec examples should be created as temporary test fixtures or curated separately before inclusion.
