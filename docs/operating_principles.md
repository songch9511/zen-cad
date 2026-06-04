# Operating Principles

- Start with `/cad-spec`.
- Spec the assembly contract before generating CAD.
- Name parameters, artifact targets, inspection checks, and repair rules before handoff.
- Use low-detail layout proxies for first-pass positioning.
- Preserve interface primitives, datums, axes, center distances, and drivetrain relationships before surface fidelity.
- Use interface signatures when layout needs standard component facts but full supplier geometry is unavailable.
- Use specialist subagents for bounded CAD subtasks when the harness supports delegation.
- Repair generated CAD by changing the smallest responsible source-level cause, then rerun the failed checks.
- Do not validate CAD by git diff, file size, screenshot, or viewer link alone.
- Use built-in interface registry facts for layout when available; record misses and use documented envelopes instead of broad catalog crawling.
- Validate machine-readable contract packages before treating them as generator-ready.
- Treat proceed approval as a lock on layout facts.
- Do not claim engineering certification from CAD geometry alone.
