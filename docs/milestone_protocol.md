# Milestone Protocol

A Zen CAD milestone is a legacy 0.7-style evidence package inside the repository. Each milestone should contain requirements, research, part classification, selected parts, custom CAD handoff, assembly metadata, validation evidence, BOM, and final report. Use `scripts/new_milestone.py` to create milestones from `milestones/_template` only when the user needs the milestone/evidence harness.

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
- CONTACT_MAP and CONNECTIONS are populated and linked to passing validation checks with `evidence_check_ids`;
- STEP/STP cache and normalized metadata exist where standard parts are used;
- CAD-kernel/export/contact/clearance checks pass with command metadata and size/hash-locked artifacts;
- validation evidence includes `cad_generation`, `step_load`, and `geometry_inspection` check types for final PASS;
- if the current environment is `ENV_BLOCKED`, validation evidence includes a passing `environment` check from the CAD runtime used to generate the final artifacts;
- BOM and final report truthfully match the validation verdict.

When a gate blocks, the final report should say `Verdict: BLOCKED` and list completed evidence, blockers, and the smallest unblock step.

New legacy milestones default to `maturity: concept` and `workflow: /cad-spec`. Use `maturity: final` only after the milestone has the source-lock, CAD export, kernel validation, BOM, and final report evidence needed for completion.
