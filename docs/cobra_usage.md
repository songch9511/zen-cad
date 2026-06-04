# CoBrA Usage

With the Zen CAD repository as the command cwd, sync skills once:

```bash
./zen-cad init --with-cobra
```

This installs the bundled skills into the CoBrA skills directory and writes `ZEN_CAD_WORKSPACE.md` beside each installed skill. The binding records the Zen CAD repository root, but it does not change CoBrA's process cwd.

## 0.8 Starting Point

In CoBrA, start new work with `/cad-spec`:

```text
Use /cad-spec to write a CAD-native layout spec for: <goal>
```

Then use `/cad-handoff` to brief the active CAD-generation route. Use `/assembly-layout` for proceed review and `/interface-signatures` for standard interface facts.

## Legacy Milestones

Legacy milestone commands still exist for compatibility:

```bash
./zen-cad new "<goal>"
./zen-cad validate --level structure milestones/<id>
./zen-cad validate --level completion milestones/<id>
```

Use them only when the user is intentionally working with the older milestone/evidence harness.
