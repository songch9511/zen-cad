# Zen CAD Harness Adapters

These adapter notes show how to use Zen CAD as a portable CAD skill pack inside agent harnesses. They are intentionally thin: each harness should keep using its own CAD generation, file, terminal, web, memory, and worker tools while Zen CAD provides optional workflow structure and final evidence gates.

Adapters included in 0.6.x:

- `cobra/`: sync bundled skills into CoBrA and run milestone work from an explicit repo path.
- `codex/`: use Zen CAD as a Codex-style skill/plugin workspace.
- `claude-code/`: use Zen CAD as a Claude Code-style skill workspace.

The adapter contract is now generate-first: expose skills, preserve repo/milestone paths, produce a concept/layout CAD artifact with the harness's available tools, and use `./zen-cad validate --level completion` only for final/release claims.
