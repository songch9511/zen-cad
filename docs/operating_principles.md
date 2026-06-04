# Operating Principles

- Use `/cad-spec` as the default starting skill.
- Write the CAD-native spec before asking a harness to generate geometry.
- Preserve assembly positioning, interface primitives, and drivetrain facts before improving surface fidelity.
- Use interface signatures for layout when full sourced STEP geometry is not yet available.
- Treat proceed approval as a lock on layout facts.
- Keep harness-specific paths and commands in adapter/handoff layers, not in core specs.
- Do not claim engineering certification from CAD geometry alone.
