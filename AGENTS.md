# Zen CAD Agent Routing

When a user asks for mechanical CAD, assembly layout, source-lock evidence,
standard part interfaces, proceed gates, or downstream CAD handoffs, use
`skills/cad-spec/SKILL.md` as the default entrypoint.

Use the narrower skills only when the task is scoped to that layer:

- `skills/assembly-layout/SKILL.md` for assembly graph, datum, axis, mate, and proceed review work.
- `skills/interface-signatures/SKILL.md` for layout-only standard component interface facts and source-lock evidence boundaries.
- `skills/cad-handoff/SKILL.md` after locked layout facts and proceed criteria are explicit.

Do not skip straight to freeform CAD generation for assembly prompts. Produce
the CAD-native contract first, then continue through layout proxy, source-lock
evidence, feature-aware build123d STEP artifacts when requested/available,
local viewer-link packaging, proceed gate, and downstream handoff when
requested.
