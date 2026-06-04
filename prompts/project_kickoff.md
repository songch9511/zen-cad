# Zen CAD Project Kickoff Prompt

Use `/cad-spec` as the top-level workflow. Treat this repository as a portable Zen CAD skill pack that leverages the host harness for actual CAD generation. Write the CAD-native spec first, then generate a low-detail layout proxy when assembly positioning matters. Require validation-script evidence only before final/release completion claims.

## Spec-First Startup

If the user starts a new agent session by stating a CAD goal, treat that as a spec-start request. Do not ask the user to choose file formats or write JSON/YAML. Use `/cad-spec` to produce a CAD-native layout spec with coordinate frames, interface primitives, proxy fidelity policy, locked layout facts, and a proceed gate.

Zen CAD is harness-native and spec-first. The first generated artifact should usually be a `layout_proxy` whose assembly positioning and interfaces are correct, even if surface quality is intentionally low. Reserve final completion claims for `maturity: final` evidence.

First response requirements:

- state assumptions and whether they are locked;
- identify standard/off-the-shelf interfaces that can be represented by interface signatures during layout;
- identify likely custom CAD parts;
- name the proceed gate and downstream handoff target;
- do not generate standard parts as final geometry without sourcing evidence.
