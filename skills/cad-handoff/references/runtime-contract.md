# Runtime Contract

Read this when a downstream CAD generator, viewer, or inspector has its own commands, geometry reference syntax, or artifact conventions.

## Rule

Core Zen CAD specs stay kernel-neutral. Tool-specific commands belong in adapter references or handoff prompts.

## Adapter Mapping

An adapter prompt should map Zen CAD concepts to the active harness:

- CAD source generation;
- explicit primary artifact path;
- generated files as derived artifacts;
- source/spec as the source of truth;
- harness-native geometry references;
- deterministic inspection commands;
- visual review or snapshot commands;
- viewer handoff;
- skipped-check reporting;
- smallest source-level repair and rerun policy.

Do not copy a full CAD runtime into Zen CAD only to satisfy a handoff. If the active harness lacks a check, state the missing capability and keep the limitation visible.
