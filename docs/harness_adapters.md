# Harness Adapters

Zen CAD 0.6.x is distributed as a harness-native CAD skill pack. The harness supplies the thing that actually makes progress: CAD generation tools, file edits, terminal execution, web/catalog lookup, memory, and optional multi-agent orchestration. Zen CAD supplies portable skills, milestone structure, source-lock/reporting conventions, and an optional final evidence gate.

The default adapter behavior is **generate first, gate later**:

1. Load the bundled skills.
2. Create or select a milestone.
3. Use the harness's available CAD stack to produce a concept/layout CAD artifact.
4. Record paths, assumptions, proxy status, and blockers.
5. Run strict Zen CAD gates only when the user asks for final/release-grade completion.

## Distribution surfaces

- `skills/`: portable Markdown skills. `/agentic-cad` remains the top-level workflow; `/spec-to-cad` remains the CAD execution handoff; `/self-evolving-producer-verifier` remains the review loop.
- `packages/zen_cad_core/`: the validation-core contract. In 0.6.x the implementation still lives in `scripts/`, `schemas/`, `templates/`, and `checklists/` so the existing repo-local CLI stays stable.
- `plugins/`: harness adapter notes for CoBrA, Codex-style agents, and Claude Code-style agents.
- `ZEN_CAD_WORKSPACE.md`: generated beside CoBrA-installed skills by `./zen-cad init --with-cobra`; records the Zen CAD repo root for installed-skill invocations.

## Adapter contract

A harness adapter should do five things:

1. Make the bundled skills discoverable to the agent.
2. Keep the Zen CAD repository path and active milestone path explicit in every CAD task brief.
3. Let the harness perform CAD generation, sourcing, file edits, execution, and worker orchestration instead of trying to reimplement those tools inside Zen CAD.
4. Treat `./zen-cad doctor` as a repo/skill sanity check; CAD toolchain `ENV_BLOCKED` warnings do not stop concept/layout generation.
5. Reserve `doctor --cad-required`, `source-lock`, and `validate --level completion` for final/release claims.

When earthtojake/text-to-cad or an equivalent STEP-first CAD skill is installed, use it as the preferred CAD execution path. Zen CAD should wrap that generation, inspection, and snapshot flow with milestone structure, source-lock rules, blocked reports, and completion gates.

CoBrA-specific adapter behavior:

1. `./zen-cad init --with-cobra` must install the three bundled skills under the CoBrA skills root.
2. The same sync must write `ZEN_CAD_WORKSPACE.md` beside each installed skill.
3. Installed skills should read that file when the current working directory is not the Zen CAD repository.
4. A missing skill or missing binding is a harness adapter problem. A missing CAD Python package is a final-gate environment problem.

Worker reports, screenshots, GLB previews, and proxy geometry are useful review artifacts. They can support a concept/layout delivery, but they are not final completion evidence.

## text-to-cad compatibility

Zen CAD is complementary to earthtojake/text-to-cad:

- Use text-to-cad for STEP-first generation.
- Use deterministic CAD inspection for refs, facts, planes, measures, mates, frames, and diffs where available.
- Use snapshots and viewer output for visual review only.
- Store resulting source paths, STEP/STL paths, assumptions, validation commands, artifact sizes, SHA-256 hashes, and blockers in the active Zen CAD milestone.
- For final PASS, record command-backed `cad_generation`, `step_load`, and `geometry_inspection` checks in `05_validation/validation_report.json`, and link CONTACT_MAP/CONNECTIONS rows to passing geometry checks with `evidence_check_ids`.
- If the validating machine cannot pass `doctor --cad-required`, record a command-backed `environment` check from the CAD runtime that actually generated the final artifacts, or report the milestone as BLOCKED.

If text-to-cad is unavailable, a harness may use build123d, CadQuery, FreeCAD, OpenSCAD, or another kernel-backed stack, but the same milestone evidence contract still applies.

## First CAD pass

Before spending time repairing the local CAD/mesh environment, let the harness try the available CAD path:

```bash
./zen-cad doctor
python3 scripts/new_milestone.py --request "<goal>"
./zen-cad validate --level structure milestones/<id>
```

Then use the harness's native tools or installed CAD skills/plugins to create source and exports under the milestone. If a local package is missing, choose another available CAD route before stopping the task.

## Final/release gate

Only when the result is being claimed as final or release-grade, run from the repository root:

```bash
./zen-cad doctor --cad-required
./zen-cad source-lock milestones/<id>
./zen-cad validate --level completion milestones/<id>
```

If this is blocked, report the shipped concept/layout artifact plus the exact final blockers instead of converting a preview into a final claim:

```bash
./zen-cad blocked-report --write milestones/<id>
```
