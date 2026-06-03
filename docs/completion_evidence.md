# Completion Evidence

Completion evidence is the final/release gate, not the first CAD gate. Zen CAD 0.6.x should produce a concept/layout CAD artifact with the harness's available tools before spending excessive time on strict environment repair.

A milestone is not final because a screenshot looks plausible. Final completion requires reproducible artifacts:

- required files exist in the milestone folder;
- JSON artifacts pass schema validation;
- `./zen-cad doctor --cad-required` can pass for final/release CAD/mesh/kernel evidence, using `--python` or `ZEN_CAD_PYTHON` when the harness needs a specific venv;
- standard/catalog parts are source-locked before custom CAD and assembly validation proceed;
- CAD source and final export paths are recorded;
- CONTACT_MAP and CONNECTIONS reference known parts;
- BOM distinguishes sourced, custom, semi-standard, and proxy parts;
- validation report states checks, results, failures, and limitations;
- final engineering report separates verified facts from assumptions.

## First CAD pass is not completion

For concept/layout work, acceptable evidence is simpler: CAD source/export paths exist, the assumptions/proxies are named, and `./zen-cad validate --level structure milestones/<id>` passes. `ENV_BLOCKED` from strict local CAD preflight is a final blocker, not a reason to return without a CAD artifact.

## Structure is not completion

`./zen-cad validate --level structure milestones/<id>` proves only that the required milestone files, JSON schemas, BOM headers, and basic milestone structure are valid.

`./zen-cad validate --level completion milestones/<id>` is the release gate. It checks the Zen CAD completion gates:

- Gate 0: doctor / environment preflight
- Gate 1: requirement normalization
- Gate 2: standard part source-lock
- Gate 3: custom CAD generation
- Gate 4: assembly contract
- Gate 5: export/cache verification
- Gate 6: CAD-kernel validation
- Gate 7: final report / BOM / evidence bundle

If completion is blocked, a truthful `BLOCKED` report is a valid milestone output. It should state completed evidence, blockers, and the smallest unblock step.

Generate one with:

```bash
./zen-cad blocked-report --write milestones/<id>
```

## Proxy isolation

Proxy artifacts are preview/debug only:

- `placeholder_proxy` parts are always completion-ineligible.
- `completion_eligible: false` must not be overridden by viewer screenshots or proxy STL files.
- standard parts need source-backed STEP/STP and source metadata.
- custom parts need source, final exports, and kernel-backed validation.
- screenshots, GLB previews, and viewer snapshots are never completion evidence.

## Maturity modes

- `concept`: generate useful CAD early; unresolved source-lock is a warning and final completion remains unavailable.
- `layout`: allow proxy/envelope assembly work while recording blockers for final evidence.
- `final`: enforce source-lock, final exports, kernel validation, BOM, and final report consistency.
