# Philosophy

Zen CAD treats CAD generation as an assembly-contract problem first. The first model should prove that parts locate, mate, move, and clear correctly. Surface detail, supplier geometry, manufacturing polish, and packaging come later.

The key artifact is the CAD-native spec: a concise statement of coordinate frames, parameters, artifact targets, datums, interface primitives, motion relationships, proxy fidelity policy, inspection plan, repair loop, locked layout facts, and proceed gate. Good specs make downstream CAD generators faster because they remove ambiguity before geometry is produced and make failed geometry cheaper to diagnose.
