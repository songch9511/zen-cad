# Operating Principles

- Start with `/cad-spec`.
- Spec the assembly contract before generating CAD.
- Use low-detail layout proxies for first-pass positioning.
- Preserve interface primitives, datums, axes, center distances, and drivetrain relationships before surface fidelity.
- Use interface signatures when layout needs standard component facts but full supplier geometry is unavailable.
- Use specialist subagents for bounded CAD subtasks when the harness supports delegation.
- Treat proceed approval as a lock on layout facts.
- Do not claim engineering certification from CAD geometry alone.
