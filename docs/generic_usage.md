# Generic Usage

Zen CAD 0.8 can be used in any agentic environment that can read Markdown and hand work to a CAD-generation toolchain.

## Spec-First Workflow

Open this repository as the workspace and start with:

```text
Use skills/cad-spec/SKILL.md to write a CAD-native spec for: <goal>
```

Then hand the spec to the active CAD generator:

```text
Use skills/cad-handoff/SKILL.md to brief the active CAD harness for a low-detail layout proxy.
```

Use `skills/assembly-layout/SKILL.md` when reviewing positioning, contacts, connections, motion relationships, or proceed readiness. Use `skills/interface-signatures/SKILL.md` when a layout needs standard component interface facts before full sourced STEP geometry exists.

## Legacy CLI

The repo-local `./zen-cad` CLI remains available for legacy milestone experiments:

```bash
./zen-cad doctor
./zen-cad new "<goal>"
./zen-cad validate --level structure milestones/<id>
```

Use completion gates only when working on legacy final-evidence packaging.
