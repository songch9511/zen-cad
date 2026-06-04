# CoBrA Adapter

Run setup with the Zen CAD repository as the command cwd:

```bash
./zen-cad init --with-cobra
```

This syncs the bundled skills into the CoBrA skills directory and writes `ZEN_CAD_WORKSPACE.md` beside each installed skill. It does not change CoBrA's process working directory.

Start new CAD work with:

```text
Use /cad-spec to write a CAD-native layout spec for: <goal>
```

Then use `/cad-handoff` to brief the active CAD-generation path. Use `/assembly-layout` for proceed review and `/interface-signatures` for standard interface facts.

Legacy milestone commands such as `./zen-cad new` and `./zen-cad validate` remain available for older final-evidence workflows.
