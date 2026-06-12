# Zen CAD Agent Routing

When a user asks for mechanical CAD, assembly layout, source-lock evidence,
standard part interfaces, proxy replacement, constrained detail CAD, proceed gates, or downstream CAD handoffs, use
`skills/cad-spec/SKILL.md` as the default entrypoint.

Use the narrower skills only when the task is scoped to that layer:

- `skills/assembly-layout/SKILL.md` for assembly graph, datum, axis, mate, and proceed review work.
- `skills/interface-signatures/SKILL.md` for layout-only standard component interface facts and source-lock evidence boundaries.
- `skills/cad-replacement/SKILL.md` for source/detail CAD replacement through interface-frame mapping and post-replacement locked-fact inspection.
- `skills/constrained-detail-cad/SKILL.md` for custom detail CAD from locked facts, protected zones, and user shape intent.
- `skills/cad-handoff/SKILL.md` after locked layout facts and proceed criteria are explicit.

Do not skip straight to freeform CAD generation for assembly prompts. Produce
the CAD-native contract first, then continue through layout proxy, source-lock
evidence, feature-aware build123d STEP artifacts when requested/available,
source/detail replacement or constrained detail generation when requested,
local viewer-link packaging, proceed gate, and downstream handoff when
requested.

When CAD generation, visual review, or repair is requested, write a Subagent
Dispatch Plan before editing geometry. Spawn bounded specialist subagents when
the harness supports them. If subagents are unavailable, state the fallback and
run the same roles sequentially in this order: layout, interface, parameter,
motion, CAD generation, visual review, engineering review, CAD review, then
repair.

When a change adds or changes user-facing commands, installation steps,
workflow entrypoints, or supported runtime behavior, update `README.md` in the
same change. Keep deeper docs in sync when they carry the operational details,
but do not treat deeper docs as a substitute for a README update.
