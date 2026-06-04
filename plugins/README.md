# Zen CAD Harness Adapters

These adapter notes show how to use Zen CAD 0.8 as a portable CAD-native spec skill pack inside agent harnesses. They are intentionally thin: each harness should keep using its own CAD generation, file, terminal, web, memory, and worker tools while Zen CAD provides focused spec, layout, interface, and handoff skills.

Adapters included in 0.8:

- `cobra/`: sync bundled skills into CoBrA and keep repository paths explicit when needed.
- `codex/`: use Zen CAD as a Codex-style skill workspace.
- `claude-code/`: use Zen CAD as a Claude Code-style skill workspace.

The adapter contract is spec-first: expose `cad-spec`, preserve locked layout facts through CAD generation, use `cad-handoff` for harness-specific commands and paths, and treat the `./zen-cad` milestone CLI as legacy final-evidence support.
