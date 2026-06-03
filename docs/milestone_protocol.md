# Milestone Protocol

A Zen CAD milestone is an independently scoped CAD job inside the repository. Each milestone should contain requirements, research, part classification, selected parts, custom CAD handoff, assembly metadata, validation evidence, BOM, and final report. Use `scripts/new_milestone.py` to create new milestones from `milestones/_template`.

Zen CAD milestones are maturity-aware and gate-based. Structure validation and completion validation are separate:

```bash
./zen-cad validate-structure milestones/<id>
./zen-cad source-lock milestones/<id>
./zen-cad validate-completion milestones/<id>
```

Required-file/schema success means the milestone scaffold is valid. It does not mean the CAD work is complete.

Completion is blocked until:

- requirements are normalized into measurable assumptions and outputs;
- every standard/catalog part is source-locked or explicitly marked as completion-ineligible proxy;
- custom CAD exports are final evidence, not proxy-only viewer/debug artifacts;
- CONTACT_MAP and CONNECTIONS are populated;
- STEP/STP cache and normalized metadata exist where standard parts are used;
- CAD-kernel/export/contact/clearance checks pass with reproducible evidence;
- BOM and final report truthfully match the validation verdict.

When a gate blocks, the final report should say `Verdict: BLOCKED` and list completed evidence, blockers, and the smallest unblock step.

New milestones default to `maturity: concept`. Use `maturity: final` only after the milestone has the source-lock, CAD export, kernel validation, BOM, and final report evidence needed for completion.
