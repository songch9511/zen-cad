# CoBrA Adapter

Run from the Zen CAD repository root:

```bash
./zen-cad init --with-cobra
```

This syncs the bundled `/agentic-cad`, `/spec-to-cad`, and `/self-evolving-producer-verifier` skills into the CoBrA skills directory. It also writes `ZEN_CAD_WORKSPACE.md` beside each installed skill so the skill can recover the Zen CAD repository root when CoBrA invokes it outside this checkout.

It does not change CoBrA's process working directory. The installed skill should use `ZEN_CAD_WORKSPACE.md` as its default root unless the user gives a different Zen CAD repo path.

For every delegated CAD task, include:

- Zen CAD repo absolute path
- active milestone path
- target maturity: `concept`, `layout`, or `final`
- allowed CAD generation/sourcing tools
- required validation command before any final claim

Minimal worker brief:

```text
Use /agentic-cad.
Zen CAD repo: /absolute/path/to/zen-cad
Active milestone: /absolute/path/to/zen-cad/milestones/<id>
Target maturity: concept|layout|final
Generate the first CAD artifact with the available harness/toolchain before spending cycles on strict env repair.
Do not claim final completion until ./zen-cad validate --level completion milestones/<id> passes from the repo root.
```

For concept/layout work, `ENV_BLOCKED` from `doctor --cad-required` is a final-gate blocker, not a reason to return without CAD. Use CoBrA file/terminal/web/worker tools to produce the best runnable artifact and report remaining blockers separately.

Troubleshooting split:

- Missing `/agentic-cad`, `/spec-to-cad`, or `/self-evolving-producer-verifier` in CoBrA means skill discovery is not set up. Run `./zen-cad init --with-cobra`.
- Missing `ZEN_CAD_WORKSPACE.md` means installed skills are not bound to this repo. Rerun `./zen-cad init --with-cobra` from the intended Zen CAD checkout.
- Missing `numpy`, `trimesh`, `build123d`, or OCP means strict final CAD evidence cannot run in that Python. It does not mean the CoBrA skill failed to install.
